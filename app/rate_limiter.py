# app/rate_limiter.py
"""
Rate limiter that increments only on UNIQUE cache-misses per IP.
Uses app.cache.get_cache / set_cache (in-memory) to store counters and seen-keys.
"""

import time
from fastapi import HTTPException
from typing import Any
from app.cache import get_cache, set_cache

# Configurable defaults
DEFAULT_WINDOW = 3600        # 1 hour window to count unique misses
DEFAULT_LIMIT = 10           # after 10 unique misses -> block
DEFAULT_BLOCK_TTL = 300      # block for 5 minutes (300s)

def _rate_key(ip: str) -> str:
    return f"rate:{ip}"

def _block_key(ip: str) -> str:
    return f"block:{ip}"

def is_blocked(ip: str) -> bool:
    """Return True if IP is currently blocked."""
    block = get_cache(_block_key(ip))
    return bool(block)

def record_cache_miss(ip: str, cache_key: str,
                      limit: int = DEFAULT_LIMIT,
                      window: int = DEFAULT_WINDOW,
                      block_ttl: int = DEFAULT_BLOCK_TTL) -> None:
    """
    Record that 'ip' attempted to fetch 'cache_key' (a cache miss).
    - Only increments the count for unique cache keys per window.
    - If limit is reached sets a block key with TTL = block_ttl and raises HTTPException(429).
    """
    # If already blocked, raise immediately
    if is_blocked(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    key = _rate_key(ip)
    data = get_cache(key)
    now = time.time()

    if data and isinstance(data, dict):
        count = int(data.get("count", 0))
        start_time = float(data.get("start_time", now))
        seen_keys = set(data.get("keys", []))
        # reset if window expired
        if now - start_time > window:
            count = 0
            start_time = now
            seen_keys = set()
    else:
        count = 0
        start_time = now
        seen_keys = set()

    # If this cache_key was already recorded in this window, do NOT increment
    if cache_key in seen_keys:
        # persist the same data (refresh TTL)
        set_cache(key, {"count": count, "start_time": start_time, "keys": list(seen_keys)}, ttl=window)
        return

    # New unique miss -> increment
    seen_keys.add(cache_key)
    count += 1

    # If reached limit, set block key and raise
    if count >= limit:
        # set a block key for block_ttl seconds
        set_cache(_block_key(ip), True, ttl=block_ttl)
        # reset the rate counter for cleanliness (optional)
        set_cache(key, {"count": 0, "start_time": now, "keys": []}, ttl=window)
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Blocked for {block_ttl} seconds.")

    # otherwise persist updated counter with TTL = window
    set_cache(key, {"count": count, "start_time": start_time, "keys": list(seen_keys)}, ttl=window)
    return

def reset_rate_for_ip(ip: str) -> None:
    """Utility: clear rate & block for an IP (useful for admin/testing)."""
    set_cache(_rate_key(ip), {"count": 0, "start_time": time.time(), "keys": []}, ttl=0)
    set_cache(_block_key(ip), False, ttl=0)



