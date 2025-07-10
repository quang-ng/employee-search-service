import time
import os
from fastapi import Request, HTTPException, Depends
from app.middleware.auth import get_current_user, User
import redis

# Redis connection using environment variable
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url, decode_responses=True)

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
