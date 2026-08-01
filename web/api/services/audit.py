"""Audit log service — records who did what and when.

Schema stored in SQLite at /var/lib/rnas/audit.db.
"""

import json
import sqlite3
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path("/var/lib/rnas/audit.db")

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    diff TEXT,
    ip_address TEXT,
    result TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
"""


_schema_ready = False
_schema_lock = threading.Lock()


def _get_db() -> sqlite3.Connection:
    global _schema_ready
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    if not _schema_ready:
        with _schema_lock:
            if not _schema_ready:
                db.executescript(SQL_SCHEMA)
                _schema_ready = True
    return db


def record(
    username: str,
    action: str,
    target: Optional[str] = None,
    diff: Optional[dict] = None,
    ip_address: str = "unknown",
    result: str = "success",
):
    """Record an audit event. Non-blocking — failures are silently logged."""
    try:
        db = _get_db()
        db.execute(
            "INSERT INTO audit_log (username, action, target, diff, ip_address, result) VALUES (?,?,?,?,?,?)",
            [username, action, target, json.dumps(diff) if diff else None, ip_address, result],
        )
        db.commit()
        db.close()
    except Exception:
        pass  # audit failure must not break the request


def query(limit: int = 50, action: Optional[str] = None) -> list[dict]:
    """Return recent audit entries."""
    try:
        db = _get_db()
        if action:
            rows = db.execute(
                "SELECT * FROM audit_log WHERE action = ? ORDER BY id DESC LIMIT ?",
                [action, limit],
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", [limit]
            ).fetchall()
        db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []
