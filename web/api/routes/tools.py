"""RNAS Tools API — ping, traceroute, RADIUS test/CoA, packet sniffer."""
import json, os, signal, subprocess, time
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth
from typing import Optional

router = APIRouter(tags=["Diagnostics"])
RADCLIENT = "/usr/bin/radclient"




def _parse_dict_lines(fh, default_vendor, attrs, vendors):
    import re
    current_vendor = default_vendor
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        vm = re.match(r"(?:VENDOR|BEGIN-VENDOR)\s+(\S+)", line)
        if vm:
            current_vendor = vm.group(1)
            vendors.add(current_vendor)
            continue
        if line.startswith("END-VENDOR"):
            current_vendor = default_vendor
            continue
        if line.startswith("$INCLUDE"):
            continue
        m = re.match(r"ATTRIBUTE\s+(\S+)\s+(\d+)\s+(\S+)", line)
        if m:
            name, oid, typ = m.group(1), m.group(2), m.group(3)
            attrs[name] = {"id": int(oid), "type": typ, "vendor": current_vendor}
            continue
        m2 = re.match(r"VALUE\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m2 and m2.group(1) in attrs:
            if "values" not in attrs[m2.group(1)]:
                attrs[m2.group(1)]["values"] = {}
            attrs[m2.group(1)]["values"][m2.group(2)] = m2.group(3)

@router.get("/dictionary")
async def get_dictionary(user=Depends(require_auth)):
    """List all RADIUS dictionary attributes"""
    import os, re
    dict_dir = "/etc/rnas/dictionary"
    attrs = {}
    vendors = set()
    if not os.path.isdir(dict_dir):
        return {"success": False, "attributes": {}, "vendors": [], "count": 0}
    # Parse standard RFC attributes first
    rfc_dir = "/usr/share/freeradius"
    import glob
    for rfc_file in sorted(glob.glob(rfc_dir + "/dictionary.rfc*")):
        with open(rfc_file, errors="ignore") as fh:
            _parse_dict_lines(fh, "Standard", attrs, vendors)
    
    # Then parse VSA dictionaries
    for fn in sorted(os.listdir(dict_dir)):
        fp = os.path.join(dict_dir, fn)
        if not os.path.isfile(fp) or fn.startswith("."):
            continue
        current_vendor = "Standard"
        with open(fp, errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                vm = re.match(r"(?:VENDOR|BEGIN-VENDOR)\s+(\S+)", line)
                if vm:
                    current_vendor = vm.group(1)
                    vendors.add(current_vendor)
                    continue
                if line.startswith("END-VENDOR"):
                    current_vendor = "Standard"
                    continue
                m = re.match(r"ATTRIBUTE\s+(\S+)\s+(\d+)\s+(\S+)", line)
                if m:
                    name, oid, typ = m.group(1), m.group(2), m.group(3)
                    if name not in attrs:  # VSA may shadow standard, prefer first
                        attrs[name] = {"id": int(oid), "type": typ, "vendor": current_vendor}
                    continue
                m2 = re.match(r"VALUE\s+(\S+)\s+(\S+)\s+(\S+)", line)
                if m2 and m2.group(1) in attrs:
                    if "values" not in attrs[m2.group(1)]:
                        attrs[m2.group(1)]["values"] = {}
                    attrs[m2.group(1)]["values"][m2.group(2)] = m2.group(3)
    if any(v == "Standard" for v in vendors) or any(a["vendor"] == "Standard" for a in attrs.values()):
        vendors.add("Standard")
    return {"success": True, "attributes": attrs, "vendors": sorted(vendors), "count": len(attrs)}

@router.get("/tools/ping")
async def ping(host: str = Query("8.8.8.8"), user=Depends(require_auth)):
    out = subprocess.run(["ping", "-c", "3", "-W", "2", host],
                         capture_output=True, text=True, timeout=10).stdout
    return {"output": out}


@router.get("/tools/trace")
async def traceroute(host: str = Query("8.8.8.8"), user=Depends(require_auth)):
    out = subprocess.run(["traceroute", "-m", "10", host],
                         capture_output=True, text=True, timeout=15).stdout
    return {"output": out}


@router.get("/tools/radius-test")
async def radius_test(
    user: str = Query("testuser"), passwd: str = Query("testpass"),
    attrs: str = Query(""), server: str = Query("192.168.0.202:1812"),
    secret: str = Query("testing123"), _auth=Depends(require_auth),
):
    pairs = [f"User-Name={user},User-Password={passwd}"]
    if attrs:
        pairs.append(attrs)
    payload = ",".join(pairs)
    out = subprocess.run(
        [RADCLIENT, "-r", "1", "-t", "3", server, "auth", secret],
        input=payload, capture_output=True, text=True, timeout=10).stdout
    return {"output": out.strip(), "payload": payload}


@router.post("/tools/radius-send")
async def radius_send(data: dict = Body(...), user=Depends(require_auth)):
    server = data.get("server", "192.168.0.202:1812")
    secret = data.get("secret", "testing123")
    port_type = data.get("type", "auth")
    attributes = data.get("attributes", [])
    pairs = [f"{a['name']}={a['value']}" for a in attributes if a.get('name') and a.get('value')]
    payload = ",".join(pairs)
    result = subprocess.run(
        [RADCLIENT, "-r", "1", "-t", "3", server, port_type, secret],
        input=payload, capture_output=True, text=True, timeout=10)
    return {"success": True, "output": result.stdout + "\n" + result.stderr,
            "payload": payload, "code": result.returncode}



@router.get("/tools/coa-pyrad")
async def coa_pyrad(user: str = Query(""), server: str = Query("127.0.0.1:3799"), secret: str = Query("testing123"), _auth=Depends(require_auth)):
    """Send CoA Disconnect-Request using pyrad library"""
    result = _pyrad_send(server, secret, DisconnectRequest, {"User-Name": user})
    return {"output": "Disconnect-ACK" if result.get("ok") and result.get("code") == DisconnectACK else "Failed", "detail": result}
@router.get("/tools/coa")
async def coa_disconnect(
    user: str = Query(""),
    server: str = Query("127.0.0.1"), port: int = Query(3799),
    secret: str = Query("testing123"), _auth=Depends(require_auth),
):
    payload = f"User-Name={user}"
    out = subprocess.run(
        [RADCLIENT, "-r", "1", "-t", "5", f"{server}:{port}", "disconnect", secret],
        input=payload, capture_output=True, text=True, timeout=10).stdout
    return {"output": out}


# ── Packet Sniffer ──

@router.get("/sniffer/status")
async def sniffer_status(user=Depends(require_auth)):
    running = subprocess.run(
        ["pgrep", "-f", "tcpdump.*rnas-sniffer"],
        capture_output=True).returncode == 0
    size = 0
    try:
        size = os.path.getsize("/tmp/rnas-sniffer.pcap")
    except OSError:
        pass
    return {"running": running, "size": size}


@router.post("/sniffer/start")
async def sniffer_start(user=Depends(require_auth)):
    subprocess.run(["pkill", "tcpdump"], capture_output=True)
    subprocess.Popen(
        ["tcpdump", "-i", "any", "-w", "/tmp/rnas-sniffer.pcap",
         "udp", "port", "1812", "or", "udp", "port", "1813", "or", "udp", "port", "3799"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"success": True, "message": "Sniffer started"}


@router.post("/sniffer/stop")
async def sniffer_stop(user=Depends(require_auth)):
    subprocess.run(["pkill", "tcpdump"], capture_output=True, timeout=5)
    return {"success": True, "message": "Sniffer stopped"}


# ── Scheduler (placeholder) ──



@router.get("/tools/dns")
async def dns_lookup(host: str, type: str = "a", user=Depends(require_auth)):
    """DNS lookup tool"""
    import subprocess
    try:
        out = subprocess.run(["dig", "+short", "-t", type, host], capture_output=True, text=True, timeout=10).stdout
        if not out.strip():
            out = subprocess.run(["nslookup", host], capture_output=True, text=True, timeout=10).stdout
        return {"output": out.strip() or "No records found"}
    except Exception as e:
        return {"output": f"Error: {e}"}

@router.post("/tools/capture")
async def capture_packets(data: dict = Body(...), user=Depends(require_auth)):
    """Start/stop packet capture"""
    action = data.get("action", "start")
    interface = data.get("interface", "ens33")
    port = data.get("port", 0)
    count = data.get("count", 100)
    pid_file = f"/var/run/rnas/tcpdump-{interface}.pid"
    
    if action == "start":
        if os.path.exists(pid_file):
            try:
                old_pid = int(open(pid_file).read().strip())
                os.kill(old_pid, 0)
                return {"status": "already_running", "pid": old_pid}
            except Exception:
                pass
        filter_expr = f"port {port}" if port else ""
        cmd = ["tcpdump", "-i", interface, "-c", str(count), "-w", f"/tmp/capture-{interface}.pcap"]
        if filter_expr: cmd += [filter_expr]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.makedirs("/var/run/rnas", exist_ok=True)
        with open(pid_file, "w") as f: f.write(str(p.pid))
        return {"status": "started", "pid": p.pid, "interface": interface, "file": f"/tmp/capture-{interface}.pcap"}
    
    elif action == "stop":
        if os.path.exists(pid_file):
            pid = int(open(pid_file).read().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                os.remove(pid_file)
                return {"status": "stopped", "pid": pid}
            except Exception:
                pass
        return {"status": "not_running"}
    
    elif action == "status":
        running = False
        if os.path.exists(pid_file):
            try:
                pid = int(open(pid_file).read().strip())
                os.kill(pid, 0)
                running = True
            except Exception:
                pass
        return {"running": running, "interface": interface}
    
    return {"status": "error", "error": "invalid action"}
