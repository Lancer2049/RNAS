"""RNAS Extended System API — logs, protocol events, scheduler, setup, certs."""

import os, re, json, glob, time, subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from api.auth import require_auth

router = APIRouter(tags=["System"])

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
    if not re.match(r"^[\w.-]+$", name):
        raise HTTPException(400, "Invalid certificate name")
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


# ── Test Results ─────────────────────────────────────────────────────────────

@router.get("/test/results")
async def test_results(user=Depends(require_auth)):
    """Return the most recent regression test output, if present."""
    candidates = [
        Path("/var/log/rnas/tests/last-regression.txt"),
        Path("/tmp/rnas-tests/last-regression.txt"),
        Path("/etc/rnas/test-results.txt"),
    ]
    for p in candidates:
        if p.exists():
            return {"regression": p.read_text(errors="replace")}
    return {"regression": ""}
