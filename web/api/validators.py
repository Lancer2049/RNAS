"""Input validators — prevent flag injection and other parameter attacks."""

import ipaddress
import re
from fastapi import HTTPException

# Domain name: letters+digits+hyphen+dot, cannot start with hyphen
_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-.]*[a-zA-Z0-9])?$")


def validate_ip_or_hostname(value: str) -> str:
    """Validate IP address or hostname. Rejects shell flag injection attacks.

    Returns the validated value unchanged on success, raises HTTPException on failure.
    """
    if value.startswith("-"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid host: parameters starting with '-' are rejected",
        )
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if _HOSTNAME_RE.match(value):
        return value
    raise HTTPException(
        status_code=400,
        detail=f"Invalid host: must be a valid IP address or hostname",
    )
