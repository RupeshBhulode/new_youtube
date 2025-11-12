# app/rate_limiter.py
import time
import json
from fastapi import HTTPException
from app.cache import get_cache, set_cache

# Rate limit key format: "rate:{ip}"
# We'll store {"count": int, "start_time": unix_ts} as the cached value.

def check_rate_limit(ip: str, limit: int, window: int = 3600):
    """
    Simple per-process rate limiter.
    - ip: client IP
    - limit: allowed requests per window
    - window: window length in seconds (default 1 hour)
    """
    key = f"rate:{ip}"
    data = get_cache(key)

    now = time.time()
    if data:
        try:
            # data expected as dict; get_cache returns Python obj
            count = int(data.get("count", 0))
            start_time = float(data.get("start_time", now))
        except Exception:
            # malformed; reset
            count = 0
            start_time = now
        if now - start_time > window:
            # reset window
            count = 0
            start_time = now
    else:
        count = 0
        start_time = now

    if count >= limit:
        # Client exceeded the allowed requests in the window
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # increment and write back (store as JSON-serializable dict)
    new_data = {"count": count + 1, "start_time": start_time}
    set_cache(key, new_data, ttl=window)
"""
import json
import time
from fastapi import HTTPException
from app.cache import redis_client  # your existing Redis client

def check_rate_limit(ip: str, limit: int, window: int = 3600):
    """
    Check and update rate limit for given IP.
    - ip: client IP
    - limit: max requests in the window
    - window: time window in seconds (default 1 hour)
    """
    key = f"rate:{ip}"
    data = redis_client.get(key)
    
    now = time.time()
    if data:
        data = json.loads(data)
        count = data["count"]
        start_time = data["start_time"]
        
        if now - start_time > window:
            # Reset window
            count = 0
            start_time = now
    else:
        count = 0
        start_time = now

    if count >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Increment count and save back to Redis
    redis_client.setex(key, window, json.dumps({"count": count + 1, "start_time": start_time}))



    """





