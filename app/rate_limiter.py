# app/rate_limiter.py
import time
from fastapi import HTTPException
from app.cache import get_cache, set_cache

def check_rate_limit(ip: str, limit: int, window: int = 3600):
    """
    Simple per-process rate limiter.
    - ip: client IP
    - limit: allowed requests in the window
    - window: time window in seconds (default 1 hour)
    """
    key = f"rate:{ip}"
    data = get_cache(key)

    now = time.time()
    if data and isinstance(data, dict):
        count = int(data.get("count", 0))
        start_time = float(data.get("start_time", now))
        # reset if window expired
        if now - start_time > window:
            count = 0
            start_time = now
    else:
        count = 0
        start_time = now

    if count >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    new_data = {"count": count + 1, "start_time": start_time}
    set_cache(key, new_data, ttl=window)






