"""In-process event bus for WebSocket push — event-driven, delta-only.

publish_state() is called from the background state-collector thread,
while WebSocket consumers live in the event loop. The subscriber list is
guarded by a lock, and each subscriber uses a thread-safe queue.Queue so
cross-thread publishes never race with connect/disconnect.
"""

import json
import queue
import threading
import time
from typing import Optional

# Current state snapshot
_state_snapshot: dict = {}
_subscribers: list = []
_lock = threading.Lock()
_last_push_time: float = 0


def register_subscriber():
    """Register a new WebSocket client. Returns a thread-safe queue."""
    q = queue.Queue(maxsize=64)
    with _lock:
        _subscribers.append(q)
    return q


def unregister_subscriber(q):
    """Remove a disconnected WebSocket client."""
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)


def publish_state(new_state: dict, force: bool = False):
    """Publish state update. Only pushes changed fields (delta).

    force=True forces a full push (e.g. for new connections).
    Guarantees at most one push per 10s even if state is static.
    """
    global _state_snapshot, _last_push_time

    delta = _diff(_state_snapshot, new_state)
    now = time.time()

    if delta or force or now - _last_push_time > 10:
        msg = json.dumps(delta or new_state)
        with _lock:
            subs = list(_subscribers)
        for q in subs:
            try:
                q.put_nowait(msg)
            except queue.Full:
                # Drop oldest so slow clients don't stall the bus
                try:
                    q.get_nowait()
                    q.put_nowait(msg)
                except queue.Empty:
                    pass
        _state_snapshot.update(new_state)
        _last_push_time = now


def get_full_state() -> dict:
    """Return the current full state snapshot (for new connections)."""
    with _lock:
        return dict(_state_snapshot)


def _diff(old: dict, new: dict) -> dict:
    """Return only the keys that changed between old and new state."""
    result = {}
    for k, v in new.items():
        if k not in old or old[k] != v:
            result[k] = v
    return result
