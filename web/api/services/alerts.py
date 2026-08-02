"""Health alert notification service — Telegram/Webhook delivery.

Configuration source: /etc/rnas/notifications.json (written by the UI via
POST /api/system/notifications). Legacy env vars RNAS_ALERT_WEBHOOK /
RNAS_ALERT_EMAIL remain as fallback for backward compatibility.
"""

import json
import os
import subprocess
from pathlib import Path

NOTIF_PATH = Path("/etc/rnas/notifications.json")


def _load_config() -> dict:
    if NOTIF_PATH.exists():
        try:
            return json.loads(NOTIF_PATH.read_text())
        except Exception:
            pass
    return {}


def _notify_telegram(token: str, chat_id: str, text: str) -> bool:
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"https://api.telegram.org/bot{token}/sendMessage",
             "-d", f"chat_id={chat_id}&text={text}"],
            capture_output=True, text=True, timeout=10,
        )
        return '"ok":true' in result.stdout
    except Exception:
        return False


def _notify_webhook(url: str, title: str, message: str, severity: str) -> bool:
    try:
        payload = json.dumps({"title": title, "message": message, "severity": severity})
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def send_alert(title: str, message: str, severity: str = "warning") -> bool:
    """Send alert via configured channels. Returns True if any channel succeeded."""
    cfg = _load_config()
    sent = False
    if cfg.get("enabled", False):
        text = f"⚠️ RNAS Alert [{severity}]\n{title}\n{message}"
        if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
            sent = _notify_telegram(cfg["telegram_bot_token"], cfg["telegram_chat_id"], text) or sent
        if cfg.get("webhook_url"):
            sent = _notify_webhook(cfg["webhook_url"], title, message, severity) or sent
    if not sent and os.environ.get("RNAS_ALERT_WEBHOOK"):
        sent = _notify_webhook(os.environ["RNAS_ALERT_WEBHOOK"], title, message, severity)
    return sent


def send_test(cfg: dict) -> list:
    """Send a test notification using the given config (not persisted)."""
    results = []
    if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id"):
        ok = _notify_telegram(cfg["telegram_bot_token"], cfg["telegram_chat_id"],
                              "RNAS Test: System is healthy")
        results.append({"channel": "telegram", "ok": ok})
    if cfg.get("webhook_url"):
        ok = _notify_webhook(cfg["webhook_url"], "RNAS Test", "System is healthy", "info")
        results.append({"channel": "webhook", "ok": ok})
    return results
