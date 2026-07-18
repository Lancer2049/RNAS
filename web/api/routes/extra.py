"""Extra API routes — interfaces, routing, tunnels, vlans, firewall, DHCP, certificates."""
import os
import re
import json
import glob
import time
import subprocess
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth
from fastapi.responses import PlainTextResponse
from services.traffic import get_history
from services.oui import lookup

router = APIRouter(tags=["Network"])
_SCRIPT_TIMEOUT = 10


# ── helpers ────────────────────────────────────────────────────────────────

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
async def add_firewall_rule(data: dict = Body(...), user=Depends(require_auth)):
    chain = data.get("chain", "rnas-hotspot")
    table = data.get("table", "nat")
    rule = data.get("rule", "")
    if not rule:
        raise HTTPException(400, "rule is required")
    family = data.get("family", "ip")
    try:
        res = subprocess.run(
            ["nft", "add", "rule", family, table, chain] + rule.split(),
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
    static_file = Path("/etc/dnsmasq.d/static.conf")
    static_file.parent.mkdir(parents=True, exist_ok=True)
    line = f"dhcp-host={mac},{ip}" + (f",{hostname}" if hostname else "") + "\n"
    with open(static_file, "a") as fh:
        fh.write(line)
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
            addrs.append({"name": parts[0], "ip": parts[2], "state": state})
    return {"addresses": addrs, "count": len(addrs)}


@router.post("/ip/addresses")
async def add_ip_address(data: dict = Body(...), user=Depends(require_auth)):
    iface = data.get("iface", "")
    ip = data.get("ip", "")
    if not iface or not ip:
        raise HTTPException(400, "iface and ip are required")
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


# ── System Log ──────────────────────────────────────────────────────────────

@router.get("/system/log")
async def system_log(lines: int = 50, unit: str = "", level: str = "", user=Depends(require_auth)):
    cmd = ["journalctl", "--no-pager", "-n", str(lines)]
    if unit:
        cmd += ["-u", unit]
    if level:
        cmd += ["-p", level]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        out = "Logs unavailable"
    return {"log": out, "lines": len(out.splitlines())}


# ── Protocol Events ─────────────────────────────────────────────────────────

@router.get("/protocol/events")
async def protocol_events(lines: int = 50, user=Depends(require_auth)):
    log_file = Path("/var/log/accel-ppp/accel-ppp.log")
    try:
        all_lines = log_file.read_text().splitlines()
    except Exception:
        return {"events": [], "count": 0}

    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
    events = []
    seen = set()
    last_cause = ""
    for line in tail:
        m = re.match(r"\[([^]]+)\]\s*:\s*(\w+):\s*(.*)", line.strip())
        if not m:
            continue
        ts, level, msg = m.group(1), m.group(2), m.group(3)

        rm = re.search(r"(send|recv)\s*\[RADIUS\(\d+\)\s*(\S+(?:-Request|-Response|-Accept|-Reject|-ACK|-NAK))\s+id=(\d+)\s*(.*)\]", msg)
        if rm:
            direction, ptype, pid, attrs = rm.group(1), rm.group(2), rm.group(3), rm.group(4).strip()
            username = ""
            ip = ""
            u = re.search(r'User-Name\s+"([^"]+)"', attrs)
            if u:
                username = u.group(1)
            i = re.search(r'Framed-IP-Address\s+(\S+?)(?:>|\s|\]|$)', attrs)
            if i:
                ip = i.group(1)
            a = re.search(r'Acct-Status-Type\s+(\S+?)(?:>|\s|\]|$)', attrs)
            acct_type = a.group(1) if a else ""
            event_key = f"{ts}_{ptype}_{pid}"
            if event_key not in seen:
                seen.add(event_key)
                events.append({
                    "time": ts, "type": ptype, "direction": direction,
                    "username": username, "ip": ip, "id": pid,
                    "acct_type": acct_type,
                    "detail": attrs[:200] if len(attrs) > 200 else attrs,
                })

        am = re.search(r"(\S+):\s+authentication\s+(succeeded|failed)", msg)
        if am:
            uname, result = am.group(1), am.group(2)
            ek = f"{ts}_auth_{uname}"
            if ek not in seen:
                seen.add(ek)
                events.append({
                    "time": ts, "type": "auth_" + result, "direction": "local",
                    "username": uname, "detail": f"Authentication {result}",
                })

        stop_cause = re.search(r'Acct-Terminate-Cause\s+([\w-]+)', msg)
        if stop_cause:
            last_cause = stop_cause.group(1)

        dm = re.search(r"(\S+):\s+disconnected", msg)
        if dm:
            iface = dm.group(1)
            cause = last_cause if last_cause else ""
            ek = f"{ts}_disc_{iface}"
            if ek not in seen:
                seen.add(ek)
                events.append({
                    "time": ts, "type": "Disconnect", "direction": "local",
                    "username": "",
                    "detail": f"{iface} disconnected ({cause})" if cause else f"{iface} disconnected",
                })

    events.reverse()
    return {"events": events, "count": len(events)}


# ── Scheduler ───────────────────────────────────────────────────────────────

@router.get("/scheduler")
async def get_scheduler(user=Depends(require_auth)):
    sched_path = Path("/etc/rnas/scheduler.json")
    try:
        tasks = json.loads(sched_path.read_text())
        if isinstance(tasks, list):
            return {"tasks": tasks, "count": len(tasks)}
        return {"tasks": tasks, "count": 0}
    except Exception as e:
        return {"tasks": [], "count": 0, "error": str(e)}


# ── Setup ───────────────────────────────────────────────────────────────────

@router.get("/setup/status")
async def setup_status(user=Depends(require_auth)):
    configured = Path("/etc/rnas/rnas.conf").exists()
    return {"configured": configured, "first_run": not configured}


@router.post("/setup/apply")
async def setup_apply(data: dict = Body(...), user=Depends(require_auth)):
    lan_ip = data.get("lan_ip", "192.168.100.1/24")
    radius_server = data.get("radius_server", "192.168.0.202")
    radius_secret = data.get("radius_secret", "testing123")
    pppoe_iface = data.get("pppoe_iface", "ens33")
    ac_name = data.get("ac_name", "RNAS")
    ip_pool_start = data.get("ip_pool_start", "192.168.100.10")
    ip_pool_end = data.get("ip_pool_end", "192.168.100.200")

    radius_cfg = (
        f"[radius]\n"
        f"auth_host={radius_server}\n"
        f"acct_host={radius_server}\n"
        f"secret={radius_secret}\n"
        f"ip_address=192.168.0.203\n"
        f"gw_ip_address=192.168.100.1\n"
    )
    Path("/etc/rnas/access.d").mkdir(parents=True, exist_ok=True)
    Path("/etc/rnas/access.d/radius.conf").write_text(radius_cfg)

    pppoe_cfg = (
        f"[pppoe]\n"
        f"interface={pppoe_iface}\n"
        f"ac-name={ac_name}\n"
        f"service-name=RNAS\n"
    )
    Path("/etc/rnas/access.d/pppoe.conf").write_text(pppoe_cfg)

    pool_cfg = (
        f"[ip-pool]\n"
        f"gateway=192.168.100.1\n"
        f"range={ip_pool_start}-{ip_pool_end}\n"
    )
    Path("/etc/rnas/access.d/ip-pool.conf").write_text(pool_cfg)

    rnas_conf = Path("/etc/rnas/rnas.conf")
    if not rnas_conf.exists():
        rnas_conf.write_text("[global]\nenabled = yes\n")

    subprocess.run(["systemctl", "restart", "rnas-accel-ppp"], capture_output=True)
    return {"status": "applied", "services": ["radius.conf", "pppoe.conf", "ip-pool.conf"]}


# ── Certificates ────────────────────────────────────────────────────────────

@router.get("/system/certificates")
async def list_certificates(user=Depends(require_auth)):
    certs = []
    for pattern in ["/etc/rnas/ssl/*.pem", "/etc/rnas/ssl/*.crt", "/etc/rnas/ssl/*.key"]:
        for fp in glob.glob(pattern):
            name = os.path.basename(fp)
            kind = "key" if name.endswith(".key") else "cert" if name.endswith(".crt") else "pem"
            certs.append({
                "name": name, "path": fp, "kind": kind,
                "size": os.path.getsize(fp),
                "modified": os.path.getmtime(fp),
            })
    return {"certificates": certs, "count": len(certs)}


@router.post("/system/certificates/generate")
async def generate_certificate(data: dict = Body(...), user=Depends(require_auth)):
    name = data.get("name", "server")
    days = data.get("days", 3650)
    cn = data.get("cn", "RNAS Server")
    key_path = f"/etc/rnas/ssl/{name}.key"
    cert_path = f"/etc/rnas/ssl/{name}.crt"
    Path("/etc/rnas/ssl").mkdir(parents=True, exist_ok=True)
    subprocess.run(["openssl", "genrsa", "-out", key_path, "2048"], capture_output=True)
    subprocess.run([
        "openssl", "req", "-new", "-x509", "-key", key_path,
        "-out", cert_path, "-days", str(days),
        "-subj", f"/CN={cn}/O=RNAS",
    ], capture_output=True)
    return {"status": "created", "key": key_path, "cert": cert_path}
