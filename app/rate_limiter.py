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
