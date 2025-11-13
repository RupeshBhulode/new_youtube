# app/rate_limiter.py
import sqlite3
import time
import threading
from fastapi import HTTPException

_DB_PATH = "rate_limits.sqlite3"
_lock = threading.Lock()

def _get_conn():
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit (
            ip TEXT PRIMARY KEY,
            count INTEGER,
            start_ts REAL
        )
    """)
    conn.commit()
    return conn

def _read_record(ip: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count, start_ts FROM rate_limit WHERE ip = ?", (ip,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"count": row[0], "start_ts": row[1]}
    return None

def _write_record(ip: str, count: int, start_ts: float):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO rate_limit (ip, count, start_ts) VALUES (?, ?, ?)",
                 (ip, count, start_ts))
    conn.commit()
    conn.close()

def _delete_record(ip: str):
    conn = _get_conn()
    conn.execute("DELETE FROM rate_limit WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()

def increment_if_allowed(ip: str, limit: int, window: int = 3600) -> bool:
    """
    Try to increment the counter for `ip`.
    Returns True if increment succeeded (i.e., remaining quota), False if limit exceeded.
    This function resets the counter if the window expired.
    """
    now = time.time()
    with _lock:
        rec = _read_record(ip)
        if not rec:
            # first request
            _write_record(ip, 1, now)
            return True

        count = rec["count"]
        start_ts = rec["start_ts"]

        if now - start_ts > window:
            # reset window
            _write_record(ip, 1, now)
            return True

        if count >= limit:
            # limit reached
            return False

        # increment
        _write_record(ip, count + 1, start_ts)
        return True

def get_remaining(ip: str, limit: int, window: int = 3600) -> dict:
    """
    Return dict {count, remaining, reset_in_seconds}
    """
    now = time.time()
    rec = _read_record(ip)
    if not rec:
        return {"count": 0, "remaining": limit, "reset_in_seconds": window}
    count = rec["count"]
    start_ts = rec["start_ts"]
    if now - start_ts > window:
        return {"count": 0, "remaining": limit, "reset_in_seconds": window}
    reset_in = int(window - (now - start_ts))
    rem = max(0, limit - count)
    return {"count": count, "remaining": rem, "reset_in_seconds": reset_in}

def ensure_allowed_or_raise(ip: str, limit: int, window: int = 3600):
    """
    Convenience: check remaining and raise HTTPException(429) if exceeded.
    NOTE: This does NOT increment. Use increment_if_allowed to increment.
    """
    rem = get_remaining(ip, limit, window)
    if rem["remaining"] <= 0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")



