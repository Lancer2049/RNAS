"""Lightweight Prometheus metrics endpoint — zero external dependencies.

Exposes core RNAS metrics in Prometheus text exposition format at
GET /metrics. Avoids prometheus-client dependency so it runs on the
deployed VM without pip installs.
"""

import time
from typing import Callable, Dict

_gauges: Dict[str, tuple[float, str]] = {}  # name -> (value, help)
_counters: Dict[str, tuple[int, str]] = {}
_start_time = time.time()


def set_gauge(name: str, value: float, help_text: str = ""):
    _gauges[name] = (float(value), help_text)


def inc_counter(name: str, help_text: str = "", delta: int = 1):
    cur, help_t = _counters.get(name, (0, help_text))
    _counters[name] = (cur + delta, help_text or help_t)


def render_metrics() -> str:
    lines = []
    for name, (value, help_text) in sorted(_gauges.items()):
        if help_text:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    for name, (value, help_text) in sorted(_counters.items()):
        if help_text:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")
    # Process-level metadata
    import os
    uptime = time.time() - _start_time
    lines.append("# HELP rnas_process_uptime_seconds Process uptime")
    lines.append("# TYPE rnas_process_uptime_seconds gauge")
    lines.append(f"rnas_process_uptime_seconds {uptime:.1f}")
    lines.append("# HELP rnas_python_gc_enabled Garbage collector enabled")
    lines.append("# TYPE rnas_python_gc_enabled gauge")
    lines.append(f"rnas_python_gc_enabled {int(__import__('gc').isenabled())}")
    return "\n".join(lines) + "\n"
