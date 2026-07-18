"""RNAS Interfaces API — interfaces, routing, tunnels, VLANs."""

import os, re, json, glob, time, subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth
from services.traffic import get_history
from services.oui import lookup

router = APIRouter(tags=["Network"])

"""Extra API routes — interfaces, routing, tunnels, vlans, firewall, DHCP, certificates."""

router = APIRouter(tags=["Network"])
_SCRIPT_TIMEOUT = 10



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


# ── Interfaces ─────────────────────────────────────────────────────────────

@router.get("/interfaces")
async def interfaces(user=Depends(require_auth)):
    out = subprocess.run(
        ["ip", "-d", "-s", "link", "show", "up"],
        capture_output=True, text=True, timeout=_SCRIPT_TIMEOUT
    ).stdout
    ifaces = []
    for block in re.split(r"\n(?=\d+: )", out):
        lines = block.strip().splitlines()
        if not lines:
            continue
        m0 = re.match(r"\d+:\s+(\S+):\s+<(.*?)>.*?mtu\s+(\d+)", lines[0])
        if not m0:
            continue
        name, flags, mtu = m0.group(1), m0.group(2), m0.group(3)
        mac, rx_b, rx_p, rx_e, rx_d = "", 0, 0, 0, 0
        tx_b, tx_p, tx_e, tx_d = 0, 0, 0, 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("link/") and not mac and not s.startswith("link/none") and not s.startswith("link/ppp"):
                mm = re.search(r"link/\S+\s+(\S+)", s)
                if mm:
                    mac = mm.group(1)
            if s.startswith("RX:") and i + 1 < len(lines):
                v = lines[i + 1].strip().split()
                if len(v) >= 4:
                    rx_b, rx_p, rx_e, rx_d = int(v[0]), int(v[1]), int(v[2]), int(v[3])
            if s.startswith("TX:") and i + 1 < len(lines):
                v = lines[i + 1].strip().split()
                if len(v) >= 4:
                    tx_b, tx_p, tx_e, tx_d = int(v[0]), int(v[1]), int(v[2]), int(v[3])
        ifaces.append({
            "name": name, "mac": mac, "mtu": int(mtu), "running": "UP" in flags,
            "rx_bytes": rx_b, "rx_packets": rx_p, "rx_errors": rx_e, "rx_dropped": rx_d,
            "tx_bytes": tx_b, "tx_packets": tx_p, "tx_errors": tx_e, "tx_dropped": tx_d,
        })
    return {"interfaces": ifaces, "count": len(ifaces)}


@router.get("/interfaces/history")
async def interface_history(name: str, range_sec: int = 3600, user=Depends(require_auth)):
    data = get_history(name, range_sec)
    return {"iface": name, "data": data, "points": len(data)}


@router.get("/traffic/history")
async def traffic_history(interface: str, period: str = "5m", user=Depends(require_auth)):
    """Return traffic history from SQLite store (5m/1h/1d aggregation)."""
    from services.traffic_store import get_history as store_history
    data = store_history(interface, period)
    return {"interface": interface, "period": period, "data": data, "points": len(data)}


@router.get("/interfaces/{name}")
async def interface_detail(name: str, user=Depends(require_auth)):
    link = subprocess.run(["ip", "link", "show", name], capture_output=True, text=True, timeout=5).stdout
    addr = subprocess.run(["ip", "-4", "addr", "show", name], capture_output=True, text=True, timeout=5).stdout
    m = re.search(r"<([^>]+)>", link)
    flags = m.group(1) if m else ""
    mac = ""
    mm = re.search(r"link/\S+\s+(\S+)", link)
    if mm:
        mac = mm.group(1)
    ip = ""
    mi = re.search(r"inet\s+(\S+)", addr)
    if mi:
        ip = mi.group(1)
    rx_b = _sysfs_stat(f"/sys/class/net/{name}/statistics/rx_bytes")
    tx_b = _sysfs_stat(f"/sys/class/net/{name}/statistics/tx_bytes")
    rx_p = _sysfs_stat(f"/sys/class/net/{name}/statistics/rx_packets")
    tx_p = _sysfs_stat(f"/sys/class/net/{name}/statistics/tx_packets")
    rx_e = _sysfs_stat(f"/sys/class/net/{name}/statistics/rx_errors")
    tx_e = _sysfs_stat(f"/sys/class/net/{name}/statistics/tx_errors")
    sess_out = subprocess.run(
        ["accel-cmd", "show", "sessions", "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"],
        capture_output=True, text=True, timeout=5,
    ).stdout
    sessions = []
    for line in sess_out.splitlines()[1:]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 9 and parts[1] == name:
            sessions.append({
                "sid": parts[0], "username": parts[2], "ip": parts[3],
                "type": parts[4], "state": parts[5], "uptime": parts[6],
                "rx": parts[7], "tx": parts[8],
            })
    return {
        "name": name, "mac": mac, "ip": ip, "flags": flags,
        "running": "UP" in flags,
        "rx_bytes": rx_b, "tx_bytes": tx_b,
        "rx_packets": rx_p, "tx_packets": tx_p,
        "rx_errors": rx_e, "tx_errors": tx_e,
        "sessions": sessions, "sessions_count": len(sessions),
    }


# ── Routing ────────────────────────────────────────────────────────────────

@router.get("/routing/status")
async def routing_status(user=Depends(require_auth)):
    ospf, bgp = {"neighbors": []}, {"peers": [], "routes": []}
    try:
        out = subprocess.run(
            ["vtysh", "-c", "show ip ospf neighbor"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        for line in out.splitlines():
            if line.strip() and not line.startswith("Neighbor") and "-" not in line[:10]:
                cols = line.split()
                if len(cols) >= 5:
                    ospf["neighbors"].append({
                        "id": cols[0], "state": cols[2],
                        "address": cols[4], "iface": cols[5] if len(cols) > 5 else "",
                    })
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["vtysh", "-c", "show bgp summary"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        for line in out.splitlines():
            cols = line.split()
            if len(cols) >= 10 and "." in cols[0]:
                bgp["peers"].append({
                    "peer": cols[0], "as": cols[2], "rcv": cols[3],
                    "sent": cols[4], "uptime": cols[8], "state": cols[9] if len(cols) > 9 else "",
                })
    except Exception:
        pass
    return {"ospf": ospf, "bgp": bgp}


# ── Tunnels ────────────────────────────────────────────────────────────────

@router.get("/tunnels")
async def tunnels(user=Depends(require_auth)):
    try:
        out = subprocess.run(
            ["ip", "-br", "-d", "link"], capture_output=True, text=True, timeout=5,
        ).stdout
        tunnels_list = []
        for line in out.splitlines():
            for t in ["gre", "ipip", "vxlan", "eoip"]:
                if t in line.lower() and "gretap" not in line.lower():
                    parts = line.split()
                    tunnels_list.append({
                        "name": parts[0], "up": "UP" in line, "type": t,
                        "local": "", "remote": "", "inner_ip": "",
                    })
        return {"tunnels": tunnels_list}
    except Exception:
        return {"tunnels": []}


# ── VLANs ───────────────────────────────────────────────────────────────────

@router.get("/vlans")
async def vlans(user=Depends(require_auth)):
    mod_loaded = False
    try:
        proc_modules = Path("/proc/modules").read_text()
        mod_loaded = "8021q" in proc_modules
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["ip", "-br", "link"], capture_output=True, text=True, timeout=5,
        ).stdout
        ifaces = []
        for line in out.splitlines():
            parts = line.split()
            if "." in parts[0]:
                name = parts[0]
                ifaces.append({
                    "name": name,
                    "id": name.split(".")[-1],
                    "up": "UP" in line,
                    "parent": name.split(".")[0],
                })
        return {
            "module": "loaded" if mod_loaded else "missing",
            "interfaces": ifaces[:20],
        }
    except Exception:
        return {"module": "unknown", "interfaces": []}

