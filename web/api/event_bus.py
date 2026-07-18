"""In-process event bus for WebSocket push — event-driven, delta-only.

Replaces the fixed 3s polling with a publish/subscribe model where
clients receive only changed state fields, reducing idle network traffic.
"""

import asyncio
import json
import time
from typing import Any

# Current state snapshot
_state_snapshot: dict = {}
_subscribers: list[asyncio.Queue] = []
_last_push_time: float = 0


def register_subscriber() -> asyncio.Queue:
    """Register a new WebSocket client. Returns a queue to read from."""
    q = asyncio.Queue(maxsize=64)
    _subscribers.append(q)
    return q


def unregister_subscriber(q: asyncio.Queue):
    """Remove a disconnected WebSocket client."""
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
        # Push to all subscribers; drop if full
        for q in _subscribers[:]:  # copy to avoid mutation during iteration
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass
        _state_snapshot.update(new_state)
        _last_push_time = now


def get_full_state() -> dict:
    """Return the current full state snapshot (for new connections)."""
    return dict(_state_snapshot)


def _diff(old: dict, new: dict) -> dict:
    """Return only the keys that changed between old and new state."""
    result = {}
    for k, v in new.items():
        if k not in old or old[k] != v:
            result[k] = v
    return result
