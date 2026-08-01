"""Health alert service — webhook/email notifications on service failures."""

import os
import json
import subprocess
from typing import Optional

WEBHOOK_URL = os.environ.get("RNAS_ALERT_WEBHOOK", "")
EMAIL_SMTP = os.environ.get("RNAS_ALERT_EMAIL", "")


async def send_alert(title: str, message: str, severity: str = "warning") -> bool:
    """Send alert via configured channels. Returns True if at least one channel succeeded."""
    sent = False
    if WEBHOOK_URL:
        try:
            payload = json.dumps({"title": title, "message": message, "severity": severity})
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", WEBHOOK_URL,
                 "-H", "Content-Type: application/json",
                 "-d", payload],
                capture_output=True, text=True, timeout=10,
            )
            sent = result.returncode == 0
        except Exception:
            pass
    return sent