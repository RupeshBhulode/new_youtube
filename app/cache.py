import sqlite3
import json
import time
import threading
from typing import Any, Optional

_DB_PATH = "cache.sqlite3"
_lock = threading.Lock()

def _get_conn():
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        value TEXT,
        expire_ts REAL
    )""")
    conn.commit()
    return conn

def get_cache(key: str) -> Optional[Any]:
    with _lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value, expire_ts FROM cache WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        val_text, expire_ts = row
        if expire_ts is not None and expire_ts <= time.time():
            # expired => delete and return None
            try:
                conn = _get_conn()
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                conn.close()
            except Exception:
                pass
            return None
        try:
            return json.loads(val_text)
        except Exception:
            return None

def set_cache(key: str, value: Any, ttl_seconds: int = None) -> bool:
    expire_ts = time.time() + ttl_seconds if ttl_seconds is not None else None
    val_text = json.dumps(value)
    with _lock:
        conn = _get_conn()
        conn.execute("INSERT OR REPLACE INTO cache (key, value, expire_ts) VALUES (?, ?, ?)",
                     (key, val_text, expire_ts))
        conn.commit()
        conn.close()
    return True

def clear_cache(key: str) -> None:
    with _lock:
        conn = _get_conn()
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()


















"""
import os
import redis
import json

# Connect to Redis Cloud
redis_client = redis.Redis(
    host="redis-14785.c16.us-east-1-2.ec2.cloud.redislabs.com",
    port=14785,
    password="387C9ui6CmnZNZWRhlv0BFmUyOpvOqPw",
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

"""





