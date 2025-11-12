# app/cache.py
import os
import redis
import json
from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError

# Read envs and set SSL boolean
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_SSL = os.getenv("REDIS_SSL", "true").lower() in ("1", "true", "yes")

# Connect to Redis Cloud (enable ssl if required)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=REDIS_SSL,
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
    except RedisError as e:
        # Log the error - don't raise to avoid 500s
        print("Warning: redis get failed:", e)
        return None

def set_cache(key: str, value, ttl: int = 3600):
    """
    Accepts any value (Pydantic models, dicts, lists, etc).
    Serializes with jsonable_encoder so it's JSON serializable.
    """
    try:
        serializable = jsonable_encoder(value)
        redis_client.setex(key, ttl, json.dumps(serializable))
    except (TypeError, ValueError) as e:
        # Serialization problem - log and continue (do not raise)
        print("Warning: caching serialization failed:", e)
    except RedisError as e:
        # Redis problem - log and continue
        print("Warning: redis set failed:", e)

