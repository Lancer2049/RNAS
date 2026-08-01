"""Dry-run validators for generated config files."""

import subprocess
from pathlib import Path
from typing import Optional

_VALIDATORS = {
    "firewall": lambda p: subprocess.run(
        ["nft", "-c", "-f", str(p)], capture_output=True, text=True, timeout=10
    ),
    "dnsmasq": lambda p: subprocess.run(
        ["dnsmasq", "--test", "--conf-file=" + str(p)], capture_output=True, text=True, timeout=10
    ),
    "ha": lambda p: subprocess.run(
        ["keepalived", "-t", "-f", str(p)], capture_output=True, text=True, timeout=10
    ),
}


def validate_config(generator_name: str, config_path: Path) -> Optional[str]:
    """Return error message string or None if the config passes validation."""
    validator = _VALIDATORS.get(generator_name)
    if validator is None:
        return None
    result = validator(config_path)
    if result.returncode != 0:
        return f"[{generator_name}] validation failed:\n{result.stderr.strip()}"
    return None
