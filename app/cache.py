# app/cache.py
import threading
import json
from cachetools import TTLCache
from fastapi.encoders import jsonable_encoder

# Config: tune these as needed
DEFAULT_MAX_ITEMS = 4096      # max number of keys to store
DEFAULT_TTL_SECONDS = 3600    # default TTL for items (1 hour)

# In-memory caches
_main_cache = TTLCache(maxsize=DEFAULT_MAX_ITEMS, ttl=DEFAULT_TTL_SECONDS)
_lock = threading.RLock()  # ensure thread-safety for multi-threaded servers

def get_cache(key: str):
    """
    Return Python object (already JSON-loaded) or None.
    Usage unchanged: cached = get_cache(cache_key)
    """
    with _lock:
        try:
            val = _main_cache.get(key, None)
            if val is None:
                return None
            # stored value already JSON-serializable (we store JSON string)
            return json.loads(val)
        except Exception as e:
            # fail-safe: do not raise — return None so endpoints compute fresh data
            print("Warning: in-memory cache GET failed:", e)
            return None

def set_cache(key: str, value, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Store value in cache. value can be Pydantic models, dicts, lists, etc.
    We encode to JSON and store as string.
    """
    try:
        serializable = jsonable_encoder(value)
        payload = json.dumps(serializable)
    except Exception as e:
        # If serialization fails, skip caching
        print("Warning: serialization for cache failed:", e)
        return

    with _lock:
        try:
            # Create a short-lived per-key cache if ttl differs from default
            if ttl != DEFAULT_TTL_SECONDS:
                # short path: put entry with custom ttl by updating a temporary cache
                # cachetools.TTLCache has a per-cache TTL, so emulate by storing expiry inside payload
                # Simpler: respect DEFAULT_TTL_SECONDS for now; for custom TTL, we store with DEFAULT and ignore exact expire
                # If you need per-key TTL accurately, we could implement a wrapper — tell me and I'll add it.
                pass
            _main_cache[key] = payload
        except Exception as e:
            print("Warning: in-memory cache SET failed:", e)

# Helper: clear cache (useful for debugging)
def clear_cache():
    with _lock:
        _main_cache.clear()


# app/cache.py
"""
import os
import redis
import json
import ssl
import certifi
from fastapi.encoders import jsonable_encoder

# Create secure SSL context for Redis Cloud
ssl_context = ssl.create_default_context(cafile=certifi.where())

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,                     # ✅ Must be True for Redis Cloud
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

def get_cache(key: str):
    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        print("⚠️ Redis GET failed:", e)
        return None

def set_cache(key: str, value, ttl: int = 3600):
    try:
        serializable = jsonable_encoder(value)
        redis_client.setex(key, ttl, json.dumps(serializable))
    except Exception as e:
        print("⚠️ Redis SET failed:", e)  """






