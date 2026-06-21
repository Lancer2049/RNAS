"""Extra API routes migrated from server.py — routing, tunnels, vlans, etc."""
import subprocess, os, time
from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import PlainTextResponse
from typing import Optional

router = APIRouter()

from oui import lookup


@router.get("/interfaces")
async def interfaces():
    """ Real-time interface stats (RouterOS-style bandwidth) """
    import re
    out = subprocess.run("ip -d -s link show up", shell=True, capture_output=True, text=True, timeout=3).stdout
    ifaces = []
    for block in re.split(r"\n(?=\d+: )", out):
        lines = block.strip().splitlines()
        if not lines: continue
        m0 = re.match(r"\d+:\s+(\S+):\s+<(.*?)>.*?mtu\s+(\d+)", lines[0])
        if not m0: continue
        name, flags, mtu = m0.group(1), m0.group(2), m0.group(3)
        mac, rx_b, rx_p, rx_e, rx_d = "", 0, 0, 0, 0
        tx_b, tx_p, tx_e, tx_d = 0, 0, 0, 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("link/") and not mac and not s.startswith("link/none") and not s.startswith("link/ppp"):
                mm = re.search(r"link/\S+\s+(\S+)", s)
                if mm: mac = mm.group(1)
            if s.startswith("RX:") and i+1 < len(lines):
                v = lines[i+1].strip().split()
                if len(v) >= 4: rx_b, rx_p, rx_e, rx_d = int(v[0]), int(v[1]), int(v[2]), int(v[3])
            if s.startswith("TX:") and i+1 < len(lines):
                v = lines[i+1].strip().split()
                if len(v) >= 4: tx_b, tx_p, tx_e, tx_d = int(v[0]), int(v[1]), int(v[2]), int(v[3])
        ifaces.append({
            "name": name, "mac": mac, "mtu": int(mtu), "running": "UP" in flags,
            "rx_bytes": rx_b, "rx_packets": rx_p, "rx_errors": rx_e, "rx_dropped": rx_d,
            "tx_bytes": tx_b, "tx_packets": tx_p, "tx_errors": tx_e, "tx_dropped": tx_d,
        })
    return {"interfaces": ifaces, "count": len(ifaces)}
@router.get("/routing/status")
async def routing_status():
    ospf, bgp = {"neighbors": []}, {"peers": [], "routes": []}
    try:
        out = subprocess.run(["vtysh", "-c", "show ip ospf neighbor"], capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            if line.strip() and not line.startswith("Neighbor") and "-" not in line[:10]:
                cols = line.split()
                if len(cols) >= 5:
                    ospf["neighbors"].append({"id": cols[0], "state": cols[2], "address": cols[4], "iface": cols[5] if len(cols) > 5 else ""})
    except: pass
    try:
        out = subprocess.run(["vtysh", "-c", "show bgp summary"], capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            cols = line.split()
            if len(cols) >= 10 and "." in cols[0]:
                bgp["peers"].append({"peer": cols[0], "as": cols[2], "rcv": cols[3], "sent": cols[4], "uptime": cols[8], "state": cols[9] if len(cols) > 9 else ""})
    except: pass
    return {"ospf": ospf, "bgp": bgp}

@router.get("/tunnels")
async def tunnels():
    try:
        out = subprocess.run(["ip", "-br", "-d", "link"], capture_output=True, text=True, timeout=5).stdout
        tunnels = []
        for line in out.splitlines():
            for t in ["gre", "ipip", "vxlan", "eoip"]:
                if t in line.lower() and "gretap" not in line.lower():
                    parts = line.split()
                    tunnels.append({"name": parts[0], "up": "UP" in line, "type": t, "local": "", "remote": "", "inner_ip": ""})
        return {"tunnels": tunnels}
    except: return {"tunnels": []}

@router.get("/vlans")
async def vlans():
    mod_loaded = subprocess.run("lsmod | grep -q 8021q", shell=True).returncode == 0
    try:
        out = subprocess.run(["ip", "-br", "link"], capture_output=True, text=True, timeout=5).stdout
        ifaces = []
        for line in out.splitlines():
            if "." in line.split()[0]:
                parts = line.split()
                name = parts[0]; parent = name.split(".")[0]
                ifaces.append({"name": name, "id": name.split(".")[-1], "up": "UP" in line, "parent": parent})
        return {"module": "loaded" if mod_loaded else "missing", "kernel": "loaded" if mod_loaded else "missing", "interfaces": ifaces[:20]}
    except: return {"module": "unknown", "kernel": "unknown", "interfaces": []}

@router.get("/netflow")
async def netflow():
    running = subprocess.run(["systemctl", "is-active", "softflowd"], capture_output=True, text=True).stdout.strip() == "active"
    return {"running": running, "collector": "192.168.0.202:2055", "interface": "ens33", "format": "netflow_v5"}

@router.get("/dhcp-relay")
async def dhcp_relay():
    running = subprocess.run(["systemctl", "is-active", "rnas-dhcp-relay"], capture_output=True, text=True).stdout.strip() == "active"
    return {"running": running, "upstream": "192.168.0.202:67", "giaddr": "192.168.100.1"}

@router.get("/hotspot/status")
async def hotspot_status():
    portal_active = os.path.exists("/opt/rnas-web/static/hotspot/login.html")
    ipt = "Active" if subprocess.run("iptables -t nat -L rnas-hotspot -n 2>/dev/null | grep -q DNAT", shell=True).returncode == 0 else "Inactive"
    return {"portal": "Active" if portal_active else "Inactive", "auth": "Active", "iptables": ipt}

@router.get("/config-export")
async def config_export():
    import json as _json
    from rnas_config import walk_config_tree
    from pathlib import Path
    config = walk_config_tree(Path("/etc/rnas"))
    return {"rnas_version": "3.0", "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "config": {k: dict(v) for k, v in config.items()}}

@router.get("/ip/arp")
async def arp_table():
    out = subprocess.run(["ip", "neigh", "show"], capture_output=True, text=True, timeout=5).stdout
    entries = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5:
            vendor = lookup(parts[4])
            entries.append({"ip": parts[0], "dev": parts[2], "mac": parts[4], "state": parts[5] if len(parts) > 5 else "", "vendor": vendor})
    return {"arp": entries}

@router.get("/ip/firewall")
async def firewall_rules():
    out = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=5).stdout
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
async def add_firewall_rule(data: dict = Body(...)):
    """Add nftables rule: { chain: str, table: str, rule: str }"""
    chain = data.get("chain", "rnas-hotspot")
    table = data.get("table", "nat")
    rule = data.get("rule", "")
    if not rule:
        raise HTTPException(400, "rule is required")
    family = data.get("family", "ip")
    try:
        res = subprocess.run(
            ["nft", "add", "rule", family, table, chain] + rule.split(),
            capture_output=True, text=True, timeout=5
        )
        if res.returncode != 0:
            raise HTTPException(400, res.stderr.strip())
        return {"ok": True, "chain": chain, "table": table, "rule": rule}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.delete("/ip/firewall")
async def delete_firewall_rule(data: dict = Body(...)):
    """Delete nftables rule by handle: { family: str, table: str, chain: str, handle: int }"""
    family = data.get("family", "ip")
    table = data.get("table", "nat")
    chain = data.get("chain", "rnas-hotspot")
    handle = data.get("handle")
    if not handle:
        raise HTTPException(400, "handle is required")
    try:
        res = subprocess.run(
            ["nft", "delete", "rule", family, table, chain, "handle", str(handle)],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode != 0:
            raise HTTPException(400, res.stderr.strip())
        return {"ok": True, "handle": handle}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/ip/firewall-full")
async def firewall_full():
    """Firewall rules with handles for delete operations"""
    chains = []
    out = subprocess.run(["nft", "-a", "list", "ruleset"], capture_output=True, text=True, timeout=5).stdout
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
                current_chain = {"name": parts[1], "table": current_table, "family": current_family, "type": "", "handle": 0, "rules": []}
                chains.append(current_chain)
            elif current_chain and "type" in s:
                current_chain["type"] = s
        elif current_chain and s and not s.startswith(("{", "}", "table", "chain")):
            # Check for handle annotation
            import re
            h = re.search(r"#\s*handle\s+(\d+)", s)
            if h:
                handle_counter = int(h.group(1))
                rule_text = re.sub(r"\s*#\s*handle\s+\d+", "", s).strip()
            else:
                rule_text = s
            current_chain["rules"].append({"text": rule_text, "handle": handle_counter if h else 0})
    return {"chains": chains}

@router.get("/ip/dhcp")
async def dhcp_leases():
    out = subprocess.run("cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo ", shell=True, capture_output=True, text=True, timeout=5).stdout
    leases = []
    for line in out.splitlines():
        if line.strip():
            parts = line.split()
            if len(parts) >= 5:
                leases.append({"timestamp": parts[0], "mac": parts[1], "ip": parts[2], "hostname": parts[3], "client_id": parts[4], "vendor": _vendor(parts[1])})
    return {"leases": leases, "count": len(leases)}



@router.get("/ip/dhcp-static")
async def dhcp_static():
    """DHCP static leases from dnsmasq config"""
    import re
    static_file = "/etc/dnsmasq.d/static.conf"
    try:
        lines = open(static_file).readlines()
    except:
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
            entries.append({"mac": mac, "ip": ip, "hostname": hostname, "enabled": not line.startswith("#")})
    return {"static": entries, "count": len(entries)}

@router.post("/ip/dhcp-static")
async def add_dhcp_static(data: dict = Body(...)):
    """Add DHCP static lease: { mac, ip, hostname? }"""
    mac = data.get("mac", "")
    ip = data.get("ip", "")
    hostname = data.get("hostname", "")
    if not mac or not ip:
        raise HTTPException(400, "mac and ip are required")
    static_file = "/etc/dnsmasq.d/static.conf"
    line = f"dhcp-host={mac},{ip}" + (f",{hostname}" if hostname else "") + "\n"
    with open(static_file, "a") as fh:
        fh.write(line)
    subprocess.run(["systemctl", "restart", "dnsmasq"], capture_output=True, timeout=5)
    return {"ok": True, "mac": mac, "ip": ip}

@router.delete("/ip/dhcp-static")
async def del_dhcp_static(data: dict = Body(...)):
    """Delete DHCP static lease by mac"""
    mac = data.get("mac", "")
    if not mac:
        raise HTTPException(400, "mac is required")
    static_file = "/etc/dnsmasq.d/static.conf"
    try:
        lines = open(static_file).readlines()
    except:
        raise HTTPException(404, "no static config")
    new_lines = [l for l in lines if mac.upper() not in l.upper()]
    if len(new_lines) == len(lines):
        raise HTTPException(404, f"mac {mac} not found")
    with open(static_file, "w") as fh:
        fh.writelines(new_lines)
    subprocess.run(["systemctl", "restart", "dnsmasq"], capture_output=True, timeout=5)
    return {"ok": True, "mac": mac}

@router.get("/ip/addresses")
async def ip_addresses():
    """Interface IP addresses"""
    out = subprocess.run("ip -4 -br addr show", shell=True, capture_output=True, text=True, timeout=3).stdout
    addrs = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1].upper() == "UP":
            addrs.append({"name": parts[0], "ip": parts[2], "state": "UP"})
        elif len(parts) >= 3:
            addrs.append({"name": parts[0], "ip": parts[2], "state": parts[1]})
    return {"addresses": addrs, "count": len(addrs)}

@router.post("/ip/addresses")
async def add_ip_address(data: dict = Body(...)):
    """Add IP to interface: { iface: str, ip: str }"""
    iface = data.get("iface", "")
    ip = data.get("ip", "")
    if not iface or not ip:
        raise HTTPException(400, "iface and ip are required")
    res = subprocess.run(["ip", "addr", "add", ip, "dev", iface], capture_output=True, text=True, timeout=5)
    if res.returncode != 0:
        raise HTTPException(400, res.stderr.strip())
    return {"ok": True, "iface": iface, "ip": ip}

@router.delete("/ip/addresses")
async def del_ip_address(data: dict = Body(...)):
    """Delete IP from interface: { iface: str, ip: str }"""
    iface = data.get("iface", "")
    ip = data.get("ip", "")
    if not iface or not ip:
        raise HTTPException(400, "iface and ip are required")
    res = subprocess.run(["ip", "addr", "del", ip, "dev", iface], capture_output=True, text=True, timeout=5)
    if res.returncode != 0:
        raise HTTPException(400, res.stderr.strip())
    return {"ok": True, "iface": iface, "ip": ip}
@router.get("/system/log")
async def system_log(lines: int = 50, unit: str = "", level: str = ""):
    cmd = ["journalctl", "--no-pager", "-n", str(lines)]
    if unit: cmd += ["-u", unit]
    if level: cmd += ["-p", level]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    return {"log": out, "lines": len(out.splitlines())}


@router.get("/scheduler")
async def get_scheduler():
    """Load scheduled tasks from JSON file"""
    import json, os
    path = "/etc/rnas/scheduler.json"
    try:
        with open(path) as fh:
            tasks = json.load(fh)
        return {"tasks": tasks, "count": len(tasks)}
    except:
        return {"tasks": [], "count": 0}

@router.post("/scheduler")
async def save_scheduler(data: dict = Body(...)):
    """Save scheduled tasks to JSON file"""
    import json, os
    tasks = data.get("tasks", [])
    path = "/etc/rnas/scheduler.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(tasks, fh, indent=2)
    return {"ok": True, "count": len(tasks)}

@router.post("/bandwidth-test")
async def bandwidth_test(data: dict = Body(...)):
    """Run iperf3 bandwidth test to a target. { target: str, port: int=5201, duration: int=5, proto: str='tcp' }"""
    target = data.get("target", "127.0.0.1")
    port = data.get("port", 5201)
    duration = data.get("duration", 5)
    proto = data.get("proto", "tcp")
    import json
    cmd = ["iperf3", "-c", target, "-p", str(port), "-t", str(duration), "-J"]
    if proto == "udp":
        cmd += ["-u", "-b", "0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
        if res.returncode == 0:
            result = json.loads(res.stdout)
            end = result.get("end", {})
            return {
                "ok": True,
                "target": target, "port": port, "proto": proto,
                "sent_mbps": round(end.get("sum_sent", {}).get("bits_per_second", 0) / 1e6, 1),
                "recv_mbps": round(end.get("sum_received", {}).get("bits_per_second", 0) / 1e6, 1),
                "retransmits": end.get("sum_sent", {}).get("retransmits", 0),
                "jitter_ms": round(end.get("sum", {}).get("jitter_ms", 0), 2),
                "lost_packets": end.get("sum", {}).get("lost_packets", 0),
                "cpu_host": end.get("cpu_utilization_percent", {}).get("host_total", 0),
                "raw": result
            }
        else:
            return {"ok": False, "error": res.stderr.strip() or res.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "iperf3 timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

