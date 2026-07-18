"""RNAS System API — systemd services, logs, network interfaces, SNMP queues."""
import os
import re
import json
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Body
from api.auth import require_auth

router = APIRouter(tags=["System"])
_SCRIPT_TIMEOUT = 10


@router.get("/system/status")
async def system_status(user=Depends(require_auth)):
    svcs = []
    for name, desc in [
        ("rnas-accel-ppp", "PPPoE/PPTP/L2TP/SSTP/IPoE Access Server"),
        ("dnsmasq", "DHCP/DNS Server"),
        ("rnas-web", "Web Dashboard"),
        ("strongswan-starter", "IPsec VPN"),
        ("wg-quick@wg0", "WireGuard VPN"),
        ("openvpn-server@server", "OpenVPN Server"),
        ("keepalived", "HA (VRRP)"),
        ("snmpd", "SNMP Monitoring"),
    ]:
        try:
            active = subprocess.run(["systemctl", "is-active", name],
                                    capture_output=True, text=True, timeout=3).stdout.strip()
        except Exception:
            active = "unknown"
        svcs.append({"name": name, "active": active, "desc": desc})

    # System resources using Python APIs instead of shell=True
    try:
        mem_parts = subprocess.run(
            ["free", "-h"], capture_output=True, text=True, timeout=3
        ).stdout.splitlines()[1].split()
        memory = f"{mem_parts[2]}/{mem_parts[1]}" if len(mem_parts) >= 3 else "N/A"
    except Exception:
        memory = "N/A"

    try:
        disk_parts = subprocess.run(
            ["df", "-h", "/"], capture_output=True, text=True, timeout=3
        ).stdout.splitlines()[1].split()
        disk = f"{disk_parts[2]}/{disk_parts[1]}" if len(disk_parts) >= 3 else "N/A"
    except Exception:
        disk = "N/A"

    # Python-native /proc reads (no subprocess shell=True)
    loadavg = Path("/proc/loadavg").read_text().strip() if Path("/proc/loadavg").exists() else "N/A"
    cpu_cores = str(os.cpu_count() or 1)
    uname = os.uname()
    kernel = uname.release
    arch = uname.machine

    try:
        osrel = Path("/etc/os-release").read_text()
        m = re.search(r'PRETTY_NAME="([^"]*)"', osrel)
        os_name = m.group(1) if m else "Debian"
    except Exception:
        os_name = "Debian"

    try:
        ut_secs = int(float(Path("/proc/uptime").read_text().split()[0]))
        ut_str = f"{ut_secs//86400}d {ut_secs%86400//3600}h {ut_secs%3600//60}m"
    except Exception:
        ut_str = "N/A"

    try:
        boot_out = subprocess.run(
            ["uptime", "-s"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
    except Exception:
        boot_out = "N/A"

    host = uname.nodename

    return {
        "services": svcs,
        "memory": memory,
        "disk": disk,
        "load": loadavg,
        "cpu_cores": cpu_cores,
        "os": os_name,
        "kernel": kernel,
        "arch": arch,
        "uptime": ut_str,
        "boot_time": boot_out,
        "hostname": host,
    }


@router.get("/system/logs")
async def system_logs(user=Depends(require_auth)):
    try:
        out = subprocess.run(["journalctl", "-u", "rnas-accel-ppp", "--no-pager", "-n", "30"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        out = "Logs unavailable"
    return {"logs": out}


@router.post("/system/service/{svc}/{action}")
async def service_action(svc: str, action: str, user=Depends(require_auth)):
    if action not in ("start", "stop", "restart"):
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    out = subprocess.run(["systemctl", action, svc], capture_output=True, text=True, timeout=10)
    return {"success": out.returncode == 0, "service": svc, "action": action,
            "output": out.stdout + out.stderr}


def _read_stat(path: str, default: str = "0") -> int:
    """Read a sysfs/ proc file safely, returning default on error."""
    try:
        val = Path(path).read_text().strip()
        return int(val) if val.isdigit() else 0
    except Exception:
        return 0


@router.get("/network/status")
async def network_status(user=Depends(require_auth)):
    interfaces = []
    out = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True, timeout=3).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            iface = parts[0]
            state = parts[1]
            if state == "UNKNOWN":
                state = "UP"
            stats = {"name": iface, "state": state, "ip": parts[2]}
            stats["rx"] = _read_stat(f"/sys/class/net/{iface}/statistics/rx_bytes")
            stats["tx"] = _read_stat(f"/sys/class/net/{iface}/statistics/tx_bytes")
            interfaces.append(stats)
    routes = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=3).stdout.strip()
    arp = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=3).stdout.strip()
    try:
        leases = Path("/var/lib/misc/dnsmasq.leases").read_text().strip()
    except Exception:
        leases = ""
    firewall = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=3).stdout.strip()
    return {"interfaces": interfaces, "routes": routes, "arp": arp, "leases": leases, "firewall": firewall}


@router.get("/radius/stats")
async def radius_stats(user=Depends(require_auth)):
    from services.accel_cmd import run_accel_cmd, parse_stat
    stat = parse_stat(run_accel_cmd("show", "stat"))
    try:
        ss_out = subprocess.run(
            ["ss", "-ulnp"], capture_output=True, text=True, timeout=3
        ).stdout
        stat["radius_port_status"] = "up" if ":1812" in ss_out else "down"
    except Exception:
        stat["radius_port_status"] = "unknown"
    return {"radius": stat}


@router.get("/queues")
async def queues(user=Depends(require_auth)):
    return {"queues": []}

@router.get("/system/health/alerts")
async def system_health_alerts(user=Depends(require_auth)):
    services = [
        ("rnas-accel-ppp", "Access Server (PPPoE/L2TP/PPTP/SSTP)"),
        ("rnas-web", "Web Dashboard API"),
        ("dnsmasq", "DHCP/DNS"),
        ("strongswan-starter", "IPsec VPN"),
        ("openvpn-server@server", "OpenVPN"),
    ]
    alerts = []
    for svc, desc in services:
        try:
            out = subprocess.run(["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=5).stdout.strip()
            if out != "active":
                sev = "critical" if out == "failed" else "warning"
                alerts.append({"service": svc, "desc": desc, "status": out, "severity": sev})
        except Exception:
            alerts.append({"service": svc, "desc": desc, "status": "unknown", "severity": "warning"})
    return {
        "total": len(alerts),
        "critical": sum(1 for a in alerts if a["severity"] == "critical"),
        "alerts": alerts,
    }

_NOTIF_PATH = Path("/etc/rnas/notifications.json")

@router.get("/system/notifications")
async def get_notification_config(user=Depends(require_auth)):
    if _NOTIF_PATH.exists():
        return json.loads(_NOTIF_PATH.read_text())
    return {"telegram_bot_token": "", "telegram_chat_id": "", "webhook_url": "", "enabled": False}

@router.post("/system/notifications")
async def set_notification_config(data: dict = Body(...), user=Depends(require_auth)):
    _NOTIF_PATH.parent.mkdir(parents=True, exist_ok=True)
    _NOTIF_PATH.write_text(json.dumps(data, indent=2))
    return {"status": "saved"}

@router.post("/system/notifications/test")
async def test_notification(data: dict = Body(...), user=Depends(require_auth)):
    results = []
    if data.get("telegram_bot_token") and data.get("telegram_chat_id"):
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST",
                 f"https://api.telegram.org/bot{data['telegram_bot_token']}/sendMessage",
                 "-d", f"chat_id={data['telegram_chat_id']}&text=RNAS+Test:+System+is+healthy"],
                capture_output=True, text=True, timeout=10,
            )
            results.append({"channel": "telegram", "ok": '"ok":true' in r.stdout})
        except Exception:
            results.append({"channel": "telegram", "ok": False})
    if data.get("webhook_url"):
        try:
            r = subprocess.run(
                ["curl", "-s", "-X", "POST", data["webhook_url"],
                 "-H", "Content-Type: application/json",
                 "-d", json.dumps({"text": "RNAS Test: System is healthy", "event": "test"})],
                capture_output=True, text=True, timeout=10,
            )
            results.append({"channel": "webhook", "ok": r.returncode == 0})
        except Exception:
            results.append({"channel": "webhook", "ok": False})
    return {"results": results}
