"""Traffic history collector — periodical interface stats sampling"""
import time, glob, threading
from collections import deque

TRAFFIC_HISTORY = {}
TRAFFIC_LOCK = threading.Lock()
HISTORY_MAX = 3600  # 5 hours at 5s intervals
RUNNING = True

def _collect():
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
            except:
                continue
            if iface in last:
                prev = last[iface]
                dt = now - prev["ts"]
                if dt > 0:
                    rx_rate = (rx - prev["rx"]) * 8 / dt
                    tx_rate = (tx - prev["tx"]) * 8 / dt
                    with TRAFFIC_LOCK:
                        if iface not in TRAFFIC_HISTORY:
                            TRAFFIC_HISTORY[iface] = deque(maxlen=HISTORY_MAX)
                        TRAFFIC_HISTORY[iface].append({
                            "ts": now, "rx": round(rx_rate, 1), "tx": round(tx_rate, 1)
                        })
            last[iface] = {"ts": now, "rx": rx, "tx": tx}

threading.Thread(target=_collect, daemon=True).start()

def get_history(iface: str, seconds: int = 3600) -> list:
    """Get traffic history for interface within time window"""
    cutoff = time.time() - seconds
    with TRAFFIC_LOCK:
        data = list(TRAFFIC_HISTORY.get(iface, []))
    return [p for p in data if p["ts"] >= cutoff]
