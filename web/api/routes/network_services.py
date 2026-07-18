"""RNAS Network Services — NetFlow, DHCP relay, Hotspot, config export."""

import os, re, json, glob, time, subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth

router = APIRouter(tags=["Network Services"])

# ── NetFlow / DHCP Relay ───────────────────────────────────────────────────

@router.get("/netflow")
async def netflow(user=Depends(require_auth)):
    try:
        running = subprocess.run(
            ["systemctl", "is-active", "softflowd"],
            capture_output=True, text=True,
        ).stdout.strip() == "active"
    except Exception:
        running = False
    return {
        "running": running,
        "collector": "192.168.0.202:2055",
        "interface": "ens33",
        "format": "netflow_v5",
    }


@router.get("/dhcp-relay")
async def dhcp_relay(user=Depends(require_auth)):
    try:
        running = subprocess.run(
            ["systemctl", "is-active", "rnas-dhcp-relay"],
            capture_output=True, text=True,
        ).stdout.strip() == "active"
    except Exception:
        running = False
    return {"running": running, "upstream": "192.168.0.202:67", "giaddr": "192.168.100.1"}


# ── Hotspot ─────────────────────────────────────────────────────────────────

@router.get("/hotspot/status")
async def hotspot_status(user=Depends(require_auth)):
    portal_active = Path("/opt/rnas-web/static/hotspot/login.html").exists()
    try:
        ipt = subprocess.run(
            ["iptables", "-t", "nat", "-L", "rnas-hotspot", "-n"],
            capture_output=True, text=True, timeout=3,
        ).stdout
        ipt_status = "Active" if "DNAT" in ipt else "Inactive"
    except Exception:
        ipt_status = "Inactive"
    return {"portal": "Active" if portal_active else "Inactive", "auth": "Active", "iptables": ipt_status}


# ── Config Export ───────────────────────────────────────────────────────────

@router.get("/config-export")
async def config_export(user=Depends(require_auth)):
    from rnas_config import walk_config_tree
    config = walk_config_tree(Path("/etc/rnas"))
    return {
        "rnas_version": "3.0",
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": {k: dict(v) for k, v in config.items()},
    }

