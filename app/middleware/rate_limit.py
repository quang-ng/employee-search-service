import time
from fastapi import Request, HTTPException, Depends
from app.middleware.auth import get_current_user, User
from collections import defaultdict
from threading import Lock

RATE_LIMIT = 10  # requests
RATE_PERIOD = 60  # seconds

# In-process thread-safe rate limiter
class InProcessRateLimiter:
    def __init__(self):
        self.lock = Lock()
        self.timestamps = defaultdict(list)  # key -> list of request times

    def is_allowed(self, key):
        now = time.monotonic()
        with self.lock:
            timestamps = self.timestamps[key]
            # Remove timestamps outside the window
            while timestamps and now - timestamps[0] > RATE_PERIOD:
                timestamps.pop(0)
            if len(timestamps) < RATE_LIMIT:
                timestamps.append(now)
                return True
            return False

rate_limiter_instance = InProcessRateLimiter()

def get_rate_limit_key(request: Request, current_user: User = None):
    if current_user:
        return f"user:{current_user.id}"
    # fallback to IP
    return f"ip:{request.client.host}"

async def rate_limiter(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    key = get_rate_limit_key(request, current_user)
    if not rate_limiter_instance.is_allowed(key):
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )
