"""Traffic history store — SQLite with ring buffer and downsampling.

Schema:
- traffic_history: raw samples (retained 24h)
- traffic_hourly: 1h aggregates (retained 7d)
- traffic_daily: 1d aggregates (retained 30d)
"""

import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path("/var/lib/rnas/traffic.db")

SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS traffic_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface TEXT NOT NULL,
    rx_bytes INTEGER NOT NULL,
    tx_bytes INTEGER NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS traffic_hourly (
    interface TEXT NOT NULL,
    rx_avg REAL NOT NULL,
    tx_avg REAL NOT NULL,
    hour TEXT NOT NULL,
    PRIMARY KEY (interface, hour)
);

CREATE TABLE IF NOT EXISTS traffic_daily (
    interface TEXT NOT NULL,
    rx_avg REAL NOT NULL,
    tx_avg REAL NOT NULL,
    date TEXT NOT NULL,
    PRIMARY KEY (interface, date)
);

-- Cleanup trigger: keep only 24h of raw data
CREATE TRIGGER IF NOT EXISTS cleanup_traffic_history
AFTER INSERT ON traffic_history
BEGIN
    DELETE FROM traffic_history WHERE timestamp < datetime('now', '-24 hours');
END;
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


def insert_sample(interface: str, rx_bytes: int, tx_bytes: int):
    """Record a traffic sample."""
    try:
        db = _get_db()
        db.execute("INSERT INTO traffic_history (interface, rx_bytes, tx_bytes) VALUES (?,?,?)",
                   [interface, rx_bytes, tx_bytes])
        db.commit()
        db.close()
    except Exception:
        pass


def get_history(interface: str, period: str = "5m") -> list[dict]:
    """Return traffic history for an interface.

    period: "5m" (raw, 1d), "1h" (hourly, 7d), "1d" (daily, 30d)
    """
    try:
        db = _get_db()
        if period == "1h":
            rows = db.execute(
                "SELECT rx_avg as rx, tx_avg as tx, "
                "CAST(strftime('%s', hour) AS INTEGER) as ts FROM traffic_hourly "
                "WHERE interface = ? AND hour > datetime('now', '-7 days') ORDER BY hour",
                [interface],
            ).fetchall()
        elif period == "1d":
            rows = db.execute(
                "SELECT rx_avg as rx, tx_avg as tx, "
                "CAST(strftime('%s', date || 'T00:00:00') AS INTEGER) as ts FROM traffic_daily "
                "WHERE interface = ? AND date > datetime('now', '-30 days') ORDER BY date",
                [interface],
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT rx_bytes as rx, tx_bytes as tx, "
                "CAST(strftime('%s', timestamp) AS INTEGER) as ts FROM traffic_history "
                "WHERE interface = ? AND timestamp > datetime('now', '-1 day') ORDER BY timestamp",
                [interface],
            ).fetchall()
        db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def run_downsample():
    """Aggregate raw samples into hourly and daily tables. Call periodically."""
    try:
        db = _get_db()
        # Hourly: average of samples in the past hour
        db.execute("""
            INSERT OR REPLACE INTO traffic_hourly (interface, rx_avg, tx_avg, hour)
            SELECT interface, AVG(rx_bytes), AVG(tx_bytes),
                   strftime('%Y-%m-%dT%H:00', timestamp)
            FROM traffic_history
            WHERE timestamp > datetime('now', '-2 hours')
            GROUP BY interface, strftime('%Y-%m-%dT%H', timestamp)
        """)
        # Daily: average of hourly samples
        db.execute("""
            INSERT OR REPLACE INTO traffic_daily (interface, rx_avg, tx_avg, date)
            SELECT interface, AVG(rx_avg), AVG(tx_avg),
                   substr(hour, 1, 10)
            FROM traffic_hourly
            WHERE hour > datetime('now', '-2 days')
            GROUP BY interface, substr(hour, 1, 10)
        """)
        db.commit()
        db.close()
    except Exception:
        pass
