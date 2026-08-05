"""RNAS Firewall API — ARP, firewall rules CRUD, reorder, toggle."""

import os, re, json, glob, time, subprocess, shlex
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth
from api.models import FirewallRule
from services.traffic import get_history
from services.oui import lookup

router = APIRouter(tags=["Firewall"])
_SCRIPT_TIMEOUT = 10


def _ensure_nat_chain(family: str, table: str, chain: str) -> None:
    """Create the nat table/chain if missing (Port Forward target)."""
    if table != "nat":
        return
    probe = subprocess.run(
        ["nft", "list", "chain", family, table, chain],
        capture_output=True, text=True, timeout=5,
    )
    if probe.returncode == 0:
        return
    subprocess.run(["nft", "add", "table", family, table], capture_output=True, text=True, timeout=5)
    hook = ["prerouting", "priority", "dstnat;"]
    if chain == "postrouting":
        hook = ["postrouting", "priority", "srcnat;"]
    subprocess.run(
        ["nft", "add", "chain", family, table, chain, "{", "type", "nat", "hook"] + hook + ["}"],
        capture_output=True, text=True, timeout=5,
    )


def _tokenize_rule(rule: str) -> list:
    """Split a rule string into nft argv, keeping comment values quoted."""
    parts = shlex.split(rule)
    argv = []
    i = 0
    while i < len(parts):
        if parts[i] == "comment" and i + 1 < len(parts):
            argv += ["comment", '"' + parts[i + 1].replace('"', "") + '"']
            i += 2
        else:
            argv.append(parts[i])
            i += 1
    return argv



def _sysfs_stat(path: str, default: int = 0) -> int:
    try:
        return int(Path(path).read_text().strip())
    except Exception:
        return default


def _vendor(mac: str) -> str:
    """Look up OUI vendor for a MAC address."""
    try:
        return lookup(mac)
    except Exception:
        return ""


# ── IP: ARP, Firewall, DHCP ────────────────────────────────────────────────

@router.get("/ip/arp")
async def arp_table(user=Depends(require_auth)):
    out = subprocess.run(
        ["ip", "neigh", "show"], capture_output=True, text=True, timeout=5,
    ).stdout
    entries = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5:
            entries.append({
                "ip": parts[0], "dev": parts[2], "mac": parts[4],
                "state": parts[5] if len(parts) > 5 else "",
                "vendor": _vendor(parts[4]),
            })
    return {"arp": entries}


@router.get("/ip/firewall")
async def firewall_rules(user=Depends(require_auth)):
    out = subprocess.run(
        ["nft", "list", "ruleset"], capture_output=True, text=True, timeout=5,
    ).stdout
    chains = []
    current_chain = None
    for line in out.splitlines():
        if line.strip().startswith("chain "):
            parts = line.split()
            if len(parts) >= 2:
                current_chain = {"name": parts[1], "rules": [], "table": "", "type": ""}
                chains.append(current_chain)
        elif current_chain is not None and line.strip() and not line.strip().startswith(("{", "}")):
            current_chain["rules"].append(line.strip())
    return {"chains": chains, "raw": out}


@router.post("/ip/firewall")
async def add_firewall_rule(data: FirewallRule = Body(...), user=Depends(require_auth)):
    chain = data.chain
    table = data.table
    rule = data.rule
    if not rule:
        raise HTTPException(400, "rule is required")
    family = data.family
    try:
        _ensure_nat_chain(family, table, chain)
        res = subprocess.run(
            ["nft", "add", "rule", family, table, chain] + _tokenize_rule(rule),
            capture_output=True, text=True, timeout=5,
        )
        if res.returncode != 0:
            raise HTTPException(400, res.stderr.strip())
        return {"ok": True, "chain": chain, "table": table, "rule": rule}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/ip/firewall")
async def delete_firewall_rule(data: dict = Body(...), user=Depends(require_auth)):
    family = data.get("family", "ip")
    table = data.get("table", "nat")
    chain = data.get("chain", "rnas-hotspot")
    handle = data.get("handle")
    if not handle:
        raise HTTPException(400, "handle is required")
    try:
        res = subprocess.run(
            ["nft", "delete", "rule", family, table, chain, "handle", str(handle)],
            capture_output=True, text=True, timeout=5,
        )
        if res.returncode != 0:
            raise HTTPException(400, res.stderr.strip())
        return {"ok": True, "handle": handle}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/ip/firewall-full")
async def firewall_full(user=Depends(require_auth)):
    chains = []
    out = subprocess.run(
        ["nft", "-a", "list", "ruleset"], capture_output=True, text=True, timeout=5,
    ).stdout
    current_chain = None
    current_table = ""
    current_family = "ip"
    handle_counter = 0
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("table"):
            parts = s.split()
            if len(parts) >= 3:
                current_family = parts[1]
                current_table = parts[2]
        if s.startswith("chain"):
            parts = s.split()
            if len(parts) >= 2:
                current_chain = {
                    "name": parts[1], "table": current_table,
                    "family": current_family, "type": "", "handle": 0, "rules": [],
                }
                chains.append(current_chain)
            elif current_chain and "type" in s:
                current_chain["type"] = s
        elif current_chain and s and not s.startswith(("{", "}", "table", "chain")):
            h = re.search(r"#\s*handle\s+(\d+)", s)
            pc = re.search(r"counter\s+packets\s+(\d+)\s+bytes\s+(\d+)", s)
            pkts = int(pc.group(1)) if pc else 0
            bytes_n = int(pc.group(2)) if pc else 0
            if h:
                handle_counter = int(h.group(1))
                rule_text = re.sub(r"\s*#\s*handle\s+\d+", "", s).strip()
            else:
                rule_text = s
            current_chain["rules"].append({
                "text": rule_text,
                "handle": handle_counter if h else 0,
                "packets": pkts,
                "bytes": bytes_n,
            })
    return {"chains": chains}


@router.put("/ip/firewall/reorder")
async def reorder_firewall_rule(data: dict = Body(...), user=Depends(require_auth)):
    chain = data.get("chain", "")
    table = data.get("table", "filter")
    family = data.get("family", "ip")
    handle = data.get("handle")
    position = data.get("position")
    if not chain or not handle:
        raise HTTPException(400, "chain and handle are required")
    try:
        subprocess.run(
            ["nft", "add", "rule", family, table, chain, "position", str(position)],
            capture_output=True, text=True, timeout=5,
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.put("/ip/firewall/{handle}/toggle")
async def toggle_firewall_rule(handle: int, data: dict = Body(...), user=Depends(require_auth)):
    enabled = data.get("enabled", True)
    chain = data.get("chain", "")
    table = data.get("table", "filter")
    family = data.get("family", "ip")
    if not chain:
        raise HTTPException(400, "chain is required")
    try:
        if enabled:
            res = subprocess.run(
                ["nft", "delete", "rule", family, table, chain, "handle", str(handle)],
                capture_output=True, text=True, timeout=5,
            )
        else:
            res = subprocess.run(
                ["nft", "add", "rule", family, table, chain, "position", str(handle), "counter", "drop"],
                capture_output=True, text=True, timeout=5,
            )
        if res.returncode != 0:
            raise HTTPException(400, res.stderr.strip())
        return {"ok": True, "enabled": enabled, "handle": handle}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/ip/dhcp")
async def dhcp_leases(user=Depends(require_auth)):
    lease_path = Path("/var/lib/misc/dnsmasq.leases")
    try:
        text = lease_path.read_text()
    except Exception:
        text = ""
    leases = []
    for line in text.splitlines():
        if line.strip():
            parts = line.split()
            if len(parts) >= 5:
                leases.append({
                    "timestamp": parts[0], "mac": parts[1], "ip": parts[2],
                    "hostname": parts[3], "client_id": parts[4],
                    "vendor": _vendor(parts[1]),
                })
    return {"leases": leases, "count": len(leases)}


@router.get("/ip/dhcp-static")
async def dhcp_static(user=Depends(require_auth)):
    static_file = Path("/etc/dnsmasq.d/static.conf")
    try:
        lines = static_file.read_text().splitlines()
    except Exception:
        lines = []
    entries = []
    for line in lines:
        line = line.strip()
        if line.startswith("dhcp-host=") or line.startswith("#"):
            content = line.replace("dhcp-host=", "").replace("#", "").strip()
            parts = [p.strip() for p in content.split(",")]
            mac = parts[0] if len(parts) > 0 else ""
            ip = parts[1] if len(parts) > 1 else ""
            hostname = parts[2] if len(parts) > 2 else ""
            entries.append({
                "mac": mac, "ip": ip, "hostname": hostname,
                "enabled": not line.startswith("#"),
            })
    return {"static": entries, "count": len(entries)}


@router.post("/ip/dhcp-static")
async def add_dhcp_static(data: dict = Body(...), user=Depends(require_auth)):
    mac = data.get("mac", "")
    ip = data.get("ip", "")
    hostname = data.get("hostname", "")
    if not mac or not ip:
        raise HTTPException(400, "mac and ip are required")
    if not re.fullmatch(r"[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}", mac):
        raise HTTPException(400, "mac must be a valid MAC address (aa:bb:cc:dd:ee:ff)")
    import ipaddress
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(400, f"Invalid IP: {ip}")
    if hostname and not re.fullmatch(r"[A-Za-z0-9._-]{1,63}", hostname):
        raise HTTPException(400, "hostname may only contain [A-Za-z0-9._-], max 63 chars")
    static_file = Path("/etc/dnsmasq.d/static.conf")
    static_file.parent.mkdir(parents=True, exist_ok=True)
    line = f"dhcp-host={mac},{ip}" + (f",{hostname}" if hostname else "") + "\n"
    try:
        lines = static_file.read_text().splitlines()
    except Exception:
        lines = []
    filtered = [l for l in lines if mac.upper() not in l.upper()]
    filtered.append(line.rstrip("\n"))
    static_file.write_text("\n".join(filtered) + "\n")
    subprocess.run(["systemctl", "restart", "dnsmasq"], capture_output=True, timeout=5)
    return {"ok": True, "mac": mac, "ip": ip}


@router.delete("/ip/dhcp-static")
async def del_dhcp_static(data: dict = Body(...), user=Depends(require_auth)):
    mac = data.get("mac", "")
    if not mac:
        raise HTTPException(400, "mac is required")
    static_file = Path("/etc/dnsmasq.d/static.conf")
    try:
        lines = static_file.read_text().splitlines()
    except Exception:
        raise HTTPException(404, "no static config")
    new_lines = [l for l in lines if mac.upper() not in l.upper()]
    if len(new_lines) == len(lines):
        raise HTTPException(404, f"mac {mac} not found")
    static_file.write_text("\n".join(new_lines) + "\n")
    subprocess.run(["systemctl", "restart", "dnsmasq"], capture_output=True, timeout=5)
    return {"ok": True, "mac": mac}


@router.get("/ip/addresses")
async def ip_addresses(user=Depends(require_auth)):
    out = subprocess.run(
        ["ip", "-4", "-br", "addr", "show"],
        capture_output=True, text=True, timeout=3,
    ).stdout
    addrs = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            state = parts[1] if parts[1].upper() != "UNKNOWN" else "UP"
            for addr in parts[2:]:
                addrs.append({"name": parts[0], "ip": addr, "state": state})
    return {"addresses": addrs, "count": len(addrs)}


@router.post("/ip/addresses")
async def add_ip_address(data: dict = Body(...), user=Depends(require_auth)):
    iface = data.get("iface", "")
    ip = data.get("ip", "")
    if not iface or not ip:
        raise HTTPException(400, "iface and ip are required")
    import ipaddress
    try:
        ipaddress.ip_interface(ip)
    except ValueError:
        raise HTTPException(400, f"Invalid IP/CIDR: {ip}")
    res = subprocess.run(["ip", "addr", "add", ip, "dev", iface], capture_output=True, text=True, timeout=5)
    if res.returncode != 0:
        raise HTTPException(400, res.stderr.strip())
    return {"ok": True, "iface": iface, "ip": ip}


@router.delete("/ip/addresses")
async def del_ip_address(data: dict = Body(...), user=Depends(require_auth)):
    iface = data.get("iface", "")
    ip = data.get("ip", "")
    if not iface or not ip:
        raise HTTPException(400, "iface and ip are required")
    res = subprocess.run(["ip", "addr", "del", ip, "dev", iface], capture_output=True, text=True, timeout=5)
    if res.returncode != 0:
        raise HTTPException(400, res.stderr.strip())
    return {"ok": True, "iface": iface, "ip": ip}

