import os
import redis
import json

# Connect to Redis Cloud
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
                      # Redis Cloud requires TLS
    decode_responses=True
)

def get_cache(key: str):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cache(key: str, value: dict, ttl: int = 3600):
    redis_client.setex(key, ttl, json.dumps(value))
