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
            capture_output=True, text=True, timeout=5,
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
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() == "active"
    except Exception:
        running = False
    relay = {}
    try:
        from rnas_config import walk_config_tree
        from pathlib import Path
        tree = walk_config_tree(Path("/etc/rnas"))
        relay = dict(tree.get("network.d.relay", {}))
    except Exception:
        pass
    return {
        "running": running,
        "upstream": relay.get("upstream", "192.168.0.202"),
        "giaddr": relay.get("giaddr", "192.168.100.1"),
        "interface": relay.get("interface", "ens33"),
        "enabled": relay.get("enabled", "no"),
        "option82": relay.get("option82", "no"),
        "circuit_id": relay.get("circuit_id", "rnas-port1"),
        "remote_id": relay.get("remote_id", "rnas"),
    }


@router.post("/dhcp-relay")
async def save_dhcp_relay(req: dict = Body(...), user=Depends(require_auth)):
    """Save DHCP relay settings to the config tree and restart the relay service."""
    from pathlib import Path
    from rnas_config import walk_config_tree, write_config_section

    root = Path("/etc/rnas")
    if not root.exists():
        raise HTTPException(status_code=503, detail="Config root /etc/rnas not found")

    keys = ["enabled", "upstream", "giaddr", "interface", "option82", "circuit_id", "remote_id"]
    values = {k: str(req[k]).strip() for k in keys if k in req}
    values["enabled"] = "yes" if values.get("enabled") in ("yes", "true", "1", "on") else "no"
    values["option82"] = "yes" if values.get("option82") in ("yes", "true", "1", "on") else "no"

    missing = [k for k in ("upstream", "giaddr", "interface") if not values.get(k)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required field(s): {', '.join(missing)}")

    try:
        # write_config_section locates files by section header name (e.g. [relay]),
        # not by tree key (network.d.relay) — pass the bare header name.
        success = write_config_section(root, "relay", values)
        if not success:
            raise HTTPException(status_code=404, detail="Relay section not found in config tree")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save relay config: {e}")

    if values["enabled"] == "yes":
        restart = subprocess.run(
            ["systemctl", "restart", "rnas-dhcp-relay"],
            capture_output=True, text=True, timeout=10,
        )
        if restart.returncode != 0:
            from services.audit import record
            record(user["username"], "relay_update", "network.d.relay", values, result="failure")
            raise HTTPException(status_code=500, detail=f"Relay restart failed: {restart.stderr.strip()[:200]}")

    from services.audit import record
    record(user["username"], "relay_update", "network.d.relay", values)
    return {"success": True, "module": "network.d.relay", "updated": values}


# ── Hotspot ─────────────────────────────────────────────────────────────────

@router.get("/hotspot/status")
async def hotspot_status(user=Depends(require_auth)):
    import os as _os
    candidate = _os.environ.get("RNAS_HOTSPOT_HTML", "")
    portal_path = Path(candidate) if candidate else Path("/opt/rnas-fastapi/static/hotspot/login.html")
    if not portal_path.exists():
        portal_path = Path("/opt/rnas-web/static/hotspot/login.html")
    portal_active = portal_path.exists()
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

