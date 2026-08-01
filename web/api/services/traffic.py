"""Traffic history collector — periodical interface stats sampling with SQLite persistence"""
import time, glob, threading, sqlite3, os
from collections import deque

DB_PATH = "/var/lib/rnas/traffic.db"
TRAFFIC_HISTORY = {}
TRAFFIC_LOCK = threading.Lock()
HISTORY_MAX = 3600
RUNNING = True

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS traffic (
        iface TEXT, ts REAL, rx_rate REAL, tx_rate REAL,
        PRIMARY KEY (iface, ts)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_traffic_iface_ts ON traffic(iface, ts)")
    conn.commit()
    conn.close()

def _prune_old(keep_seconds=86400):
    """Delete data older than keep_seconds"""
    cutoff = time.time() - keep_seconds
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM traffic WHERE ts < ?", (cutoff,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _load_recent(iface: str, seconds: int = 3600):
    """Load recent data from SQLite into memory on startup"""
    cutoff = time.time() - seconds
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT ts, rx_rate, tx_rate FROM traffic WHERE iface=? AND ts > ? ORDER BY ts",
            (iface, cutoff)
        ).fetchall()
        conn.close()
        return [{"ts": r[0], "rx": r[1], "tx": r[2]} for r in rows]
    except Exception:
        return []

def _collect():
    _init_db()
    last_write = 0
    last = {}
    while RUNNING:
        time.sleep(5)
        now = time.time()
        for rx_path in glob.glob("/sys/class/net/*/statistics/rx_bytes"):
            iface = rx_path.split("/")[4]
            tx_path = rx_path.replace("rx_bytes", "tx_bytes")
            try:
                rx = int(open(rx_path).read().strip())
                tx = int(open(tx_path).read().strip())
            except Exception:
                continue
            if iface in last:
                prev = last[iface]
                dt = now - prev["ts"]
                if dt > 0:
                    rx_rate = (rx - prev["rx"]) * 8 / dt
                    tx_rate = (tx - prev["tx"]) * 8 / dt
                    point = {"ts": now, "rx": round(rx_rate, 1), "tx": round(tx_rate, 1)}
                    with TRAFFIC_LOCK:
                        if iface not in TRAFFIC_HISTORY:
                            TRAFFIC_HISTORY[iface] = deque(maxlen=HISTORY_MAX)
                        TRAFFIC_HISTORY[iface].append(point)
            last[iface] = {"ts": now, "rx": rx, "tx": tx}

        # Batch write to SQLite every 30s
        if now - last_write >= 30:
            try:
                conn = sqlite3.connect(DB_PATH)
                with TRAFFIC_LOCK:
                    for iface, points in TRAFFIC_HISTORY.items():
                        for p in points:
                            conn.execute("INSERT OR IGNORE INTO traffic (iface, ts, rx_rate, tx_rate) VALUES (?,?,?,?)",
                                        (iface, p["ts"], p["rx"], p["tx"]))
                conn.commit()
                conn.close()
                last_write = now
                _prune_old()
            except Exception:
                pass

# Start collector once per process — module import can happen multiple times
# (e.g. uvicorn --reload, multiple routes importing this module).
_collector_started = False
if not _collector_started:
    threading.Thread(target=_collect, daemon=True).start()
    _collector_started = True

def get_history(iface: str, seconds: int = 3600) -> list:
    """Get traffic history for interface within time window"""
    cutoff = time.time() - seconds
    with TRAFFIC_LOCK:
        data = list(TRAFFIC_HISTORY.get(iface, []))
    mem_data = [p for p in data if p["ts"] >= cutoff]

    # Also load from SQLite for older data
    if seconds > 300:  # Only query DB for longer ranges
        db_data = _load_recent(iface, seconds)
        # Merge: prefer memory data (newer), append DB data for older
        seen_ts = {p["ts"] for p in mem_data}
        for p in db_data:
            if p["ts"] not in seen_ts:
                mem_data.append(p)
        mem_data.sort(key=lambda x: x["ts"])

    return mem_data
