# db.py — tiny SQLite cache so predictions aren't recomputed on every page load.
import json
import os
import sqlite3
import time

DB_PATH = os.getenv("BIXPIX_DB", os.path.join(os.path.dirname(__file__), "bixpix.db"))


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        " key TEXT PRIMARY KEY,"
        " payload TEXT NOT NULL,"
        " fetched_at REAL NOT NULL)"
    )
    return conn


def get(key: str, max_age_seconds: float):
    """Return the cached JSON value for key, or None if missing/older than max_age_seconds."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT payload, fetched_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
    if not row:
        return None
    payload, fetched_at = row
    if time.time() - fetched_at > max_age_seconds:
        return None
    return json.loads(payload)


def set(key: str, value) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, payload, fetched_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
