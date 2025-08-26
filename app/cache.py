import json 
import redis
# Connect to Redis locally 
redis_client = redis.Redis(
     host="localhost", port=6379, db=0, decode_responses=True )
def get_cache(key: str): 
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached) 
    return None
    
def set_cache(key: str, value: dict, ttl: int = 3600): 
    redis_client.setex(key, ttl, json.dumps(value))