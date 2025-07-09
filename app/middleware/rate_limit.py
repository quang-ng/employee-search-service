import time
from fastapi import Request, HTTPException, Depends
from app.middleware.auth import get_current_user, User
import redis

# Redis connection (adjust host/port/db as needed)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

RATE_LIMIT = 10  # requests
RATE_PERIOD = 60  # seconds


def get_rate_limit_key(request: Request, current_user: User = None):
    if current_user:
        return f"user:{current_user.id}"
    # fallback to IP
    return f"ip:{request.client.host}"


async def rate_limiter(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    redis_key = f"rl:user:{current_user.id}"
    # Increment the counter
    current = redis_client.incr(redis_key)
    if current == 1:
        # Set expiry on first request
        redis_client.expire(redis_key, RATE_PERIOD)
    if current > RATE_LIMIT:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )
