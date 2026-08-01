"""Health check utilities for config apply safety.

After applying new configs, verify that core services are still alive.
If not, trigger automatic rollback to the pre-apply snapshot.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

SNAPSHOT_DIR = Path("/etc/rnas/snapshots")
DEFAULT_ROOT = "/etc/rnas"


def check_core_services() -> dict[str, bool]:
    """Return {service_name: alive} for each core service."""
    results = {}
    try:
        rc = subprocess.run(["pgrep", "-x", "accel-pppd"], capture_output=True, timeout=5)
        results["accel-ppp"] = rc.returncode == 0
    except Exception:
        results["accel-ppp"] = False

    try:
        rc = subprocess.run(["pgrep", "-x", "dnsmasq"], capture_output=True, timeout=5)
        results["dnsmasq"] = rc.returncode == 0
    except Exception:
        results["dnsmasq"] = False

    return results


def health_check() -> bool:
    """Return True if all core checks pass."""
    services = check_core_services()
    return all(services.values()) if services else False


def restore_snapshot(snapshot_name: str) -> bool:
    """Restore config files from a snapshot. Returns True on success."""
    import shutil

    source = SNAPSHOT_DIR / snapshot_name
    if not source.exists():
        return False

    ignored_dirs = {"snapshots", "backup", "archive", "bak"}
    try:
        for f in source.rglob("*.conf"):
            if any(part in ignored_dirs for part in f.relative_to(source).parts):
                continue
            rel = f.relative_to(source)
            target = Path(DEFAULT_ROOT) / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.read_text())
        return True
    except Exception:
        return False
