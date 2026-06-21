"""RNAS Tools API — ping, traceroute, RADIUS test/CoA, packet sniffer."""
import json, os, subprocess, time
from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional

router = APIRouter()
RADCLIENT = "/usr/bin/radclient"



@router.get("/dictionary")
async def get_dictionary():
    """List all RADIUS dictionary attributes"""
    import os, re
    dict_dir = "/etc/rnas/dictionary"
    attrs = {}
    vendors = set()
    if not os.path.isdir(dict_dir):
        return {"success": False, "attributes": {}, "vendors": [], "count": 0}
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
                # Track vendor from VENDOR and BEGIN-VENDOR declarations
                vm = re.match(r"(?:VENDOR|BEGIN-VENDOR)\s+(\S+)", line)
                if vm:
                    current_vendor = vm.group(1)
                    vendors.add(current_vendor)
                    continue
                if line.startswith("END-VENDOR"):
                    current_vendor = "Standard"
                    continue
                # Parse: ATTRIBUTE <name> <id> <type>
                m = re.match(r"ATTRIBUTE\s+(\S+)\s+(\d+)\s+(\S+)", line)
                if m:
                    name, oid, typ = m.group(1), m.group(2), m.group(3)
                    attrs[name] = {"id": int(oid), "type": typ, "vendor": current_vendor}
                    continue
                # Parse: VALUE <attr> <name> <value>
                m2 = re.match(r"VALUE\s+(\S+)\s+(\S+)\s+(\S+)", line)
                if m2 and m2.group(1) in attrs:
                    if "values" not in attrs[m2.group(1)]:
                        attrs[m2.group(1)]["values"] = {}
                    attrs[m2.group(1)]["values"][m2.group(2)] = m2.group(3)
    return {"success": True, "attributes": attrs, "vendors": sorted(vendors), "count": len(attrs)}

@router.get("/tools/ping")
async def ping(host: str = Query("8.8.8.8")):
    out = subprocess.run(["ping", "-c", "3", "-W", "2", host],
                         capture_output=True, text=True, timeout=10).stdout
    return {"output": out}


@router.get("/tools/trace")
async def traceroute(host: str = Query("8.8.8.8")):
    out = subprocess.run(["traceroute", "-m", "10", host],
                         capture_output=True, text=True, timeout=15).stdout
    return {"output": out}


@router.get("/tools/radius-test")
async def radius_test(
    user: str = Query("testuser"), passwd: str = Query("testpass"),
    attrs: str = Query(""), server: str = Query("192.168.0.202:1812"),
    secret: str = Query("testing123"),
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
async def radius_send(data: dict = Body(...)):
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


@router.get("/tools/coa")
async def coa_disconnect(
    user: str = Query(""),
    server: str = Query("127.0.0.1"), port: int = Query(3799),
    secret: str = Query("testing123"),
):
    out = subprocess.run(
        f"echo 'User-Name={user}' | radclient -r 1 -t 5 {server}:{port} disconnect {secret}",
        shell=True, capture_output=True, text=True, timeout=10).stdout
    return {"output": out}


# ── Packet Sniffer ──

@router.get("/sniffer/status")
async def sniffer_status():
    running = subprocess.run("pgrep -f 'tcpdump.*rnas-sniffer'",
                              shell=True, capture_output=True).returncode == 0
    size = 0
    try:
        size = os.path.getsize("/tmp/rnas-sniffer.pcap")
    except OSError:
        pass
    return {"running": running, "size": size}


@router.post("/sniffer/start")
async def sniffer_start():
    subprocess.run("pkill tcpdump 2>/dev/null", shell=True)
    subprocess.run(
        "nohup tcpdump -i any -w /tmp/rnas-sniffer.pcap udp port 1812 or udp port 1813 or udp port 3799 &",
        shell=True, timeout=5)
    return {"success": True, "message": "Sniffer started"}


@router.post("/sniffer/stop")
async def sniffer_stop():
    subprocess.run("pkill tcpdump 2>/dev/null", shell=True, timeout=5)
    return {"success": True, "message": "Sniffer stopped"}


# ── Scheduler (placeholder) ──


