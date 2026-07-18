"""Background state collector — adaptive interval, event-driven push.

Idle (no active sessions):   5s interval
Active (sessions > 0):       1s interval
"""

import os
import re
import subprocess
import threading
import time

_ACCEL_CMD = os.environ.get("RNAS_ACCEL_CMD", "accel-cmd")


def start_collector():
    """Start the background state collector thread (daemon)."""
    t = threading.Thread(target=_collect_loop, daemon=True, name="rnas-state-collector")
    t.start()


def _collect_loop():
    from event_bus import publish_state
    from services.alerts import send_alert
    import asyncio

    idle_interval = 5.0
    active_interval = 1.0
    last_alert_time = 0.0

    while True:
        try:
            state = _gather_state()
            publish_state(state)

            now = time.time()
            if not _check_core_services() and now - last_alert_time > 300:
                asyncio.run(send_alert("RNAS Core Down", "accel-ppp or dnsmasq not running", "critical"))
                last_alert_time = now
        except Exception:
            pass

        interval = active_interval if state.get("sessions_active", 0) > 0 else idle_interval
        time.sleep(interval)


def _check_core_services() -> bool:
    try:
        rc = subprocess.run(["pgrep", "-x", "accel-pppd"], capture_output=True, timeout=5)
        return rc.returncode == 0
    except Exception:
        return False


def _sample_traffic():
    try:
        from services.traffic_store import insert_sample
        from pathlib import Path
        for iface in ["ens33", "eth0", "br-lan"]:
            rx_p = Path(f"/sys/class/net/{iface}/statistics/rx_bytes")
            tx_p = Path(f"/sys/class/net/{iface}/statistics/tx_bytes")
            if rx_p.exists() and tx_p.exists():
                insert_sample(iface, int(rx_p.read_text().strip()), int(tx_p.read_text().strip()))
    except Exception:
        pass


def _gather_state() -> dict:
    state = _gather()
    _sample_traffic()
    return state


def _gather() -> dict:
    """Collect system state from accel-cmd and /proc."""
    state = {
        "uptime": "N/A", "cpu": "N/A", "mem": "N/A",
        "radius_state": "unknown", "auth_sent": 0, "acct_sent": 0,
        "sessions_active": 0, "sessions": [], "sessions_count": 0,
    }

    try:
        stat_raw = subprocess.run(
            [_ACCEL_CMD, "show", "stat"],
            capture_output=True, text=True, timeout=3
        ).stdout

        patterns = [
            ("uptime", r"uptime:\s*(\S+)"),
            ("cpu", r"cpu:\s*(\S+)"),
            ("mem", r"mem\(rss/virt\):\s*(\S+)"),
            ("radius_state", r"state:\s*(\S+)"),
            ("auth_sent", r"auth sent:\s*(\d+)"),
            ("acct_sent", r"acct sent:\s*(\d+)"),
            ("sessions_active", r"sessions:.*?active:\s*(\d+)"),
        ]
        for key, pat in patterns:
            m = re.search(pat, stat_raw, re.DOTALL)
            if m:
                state[key] = m.group(1)

        sessions_raw = subprocess.run(
            [_ACCEL_CMD, "show", "sessions",
             "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"],
            capture_output=True, text=True, timeout=3
        ).stdout

        sessions = []
        for line in sessions_raw.splitlines()[1:]:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 9 and parts[0] and not parts[0].startswith("sid") and not parts[0].startswith("-"):
                sessions.append({
                    "sid": parts[0], "ifname": parts[1], "username": parts[2],
                    "ip": parts[3], "type": parts[4], "state": parts[5],
                    "uptime_raw": parts[6], "rx_bytes_raw": parts[7], "tx_bytes_raw": parts[8],
                })
        state["sessions"] = sessions
        state["sessions_count"] = len(sessions)
    except Exception:
        pass

    return state
