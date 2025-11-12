# app/cache.py
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
        print("⚠️ Redis SET failed:", e)


