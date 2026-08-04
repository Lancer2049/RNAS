"""Background alert notifier — polls health alerts and sends notifications
for new or escalated alerts (deduped until recovery)."""

import fcntl
import threading
import time
from pathlib import Path

from services.alerts import send_alert

POLL_INTERVAL = 60
LOCK_FILE = Path("/var/run/rnas-alert-worker.lock")
_alerts_seen: dict = {}
_lock = threading.Lock()
_lock_fd = None


def _alert_key(a: dict) -> str:
    return f"{a.get('type')}-{a.get('service')}"


def _check_once() -> None:
    from routes.system import collect_alerts
    alerts = collect_alerts()
    new_ones = []
    with _lock:
        for a in alerts:
            key = _alert_key(a)
            sev = a.get("severity", "warning")
            prev = _alerts_seen.get(key)
            if prev is None or (prev != "critical" and sev == "critical"):
                _alerts_seen[key] = sev
                new_ones.append(a)
        active_keys = {_alert_key(a) for a in alerts}
        for key in list(_alerts_seen):
            if key not in active_keys:
                del _alerts_seen[key]
    for a in new_ones:
        send_alert(a.get("title", "RNAS alert"),
                   a.get("message", ""),
                   a.get("severity", "warning"))


def _loop() -> None:
    while True:
        try:
            _check_once()
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)


def start_alert_worker() -> None:
    """Start the worker thread, guarded by a process-wide flock so a
    multi-worker uvicorn deployment does not spawn duplicate notifiers."""
    global _lock_fd
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        _lock_fd = LOCK_FILE.open("w")
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        return
    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
