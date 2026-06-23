"""RNAS System API — systemd services, logs, network interfaces, SNMP queues."""
import subprocess
from fastapi import APIRouter, HTTPException, Body

router = APIRouter()


@router.get("/system/status")
async def system_status():
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

    mem = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.splitlines()[1].split()
    disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.splitlines()[1].split()
    # system resource details
    loadavg = subprocess.run("cat /proc/loadavg", shell=True, capture_output=True, text=True).stdout.strip()
    cpu_cores = subprocess.run("nproc", shell=True, capture_output=True, text=True).stdout.strip()
    os_name = subprocess.run('grep PRETTY_NAME /etc/os-release 2>/dev/null | cut -d= -f2', shell=True, capture_output=True, text=True).stdout.strip().replace('"', '')
    kernel = subprocess.run("uname -r", shell=True, capture_output=True, text=True).stdout.strip()
    arch = subprocess.run("uname -m", shell=True, capture_output=True, text=True).stdout.strip()
    uptime_str = subprocess.run("cat /proc/uptime | awk '{print $1}'", shell=True, capture_output=True, text=True).stdout.strip()
    boot = subprocess.run("who -b | awk '{print $3,$4}'", shell=True, capture_output=True, text=True).stdout.strip()
    host = subprocess.run("hostname", shell=True, capture_output=True, text=True).stdout.strip()
    try:
        ut = int(float(uptime_str))
        ut_str = f"{ut//86400}d {ut%86400//3600}h {ut%3600//60}m"
    except:
        ut_str = "N/A"
    return {
        "services": svcs,
        "memory": f"{mem[2]}/{mem[1]}" if len(mem) >= 3 else "N/A",
        "disk": f"{disk[2]}/{disk[1]}" if len(disk) >= 3 else "N/A",
        "load": loadavg,
        "cpu_cores": cpu_cores,
        "os": os_name or "Debian",
        "kernel": kernel,
        "arch": arch,
        "uptime": ut_str,
        "boot_time": boot,
        "hostname": host,
    }


@router.get("/system/logs")
async def system_logs():
    try:
        out = subprocess.run(["journalctl", "-u", "rnas-accel-ppp", "--no-pager", "-n", "30"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        out = "Logs unavailable"
    return {"logs": out}


@router.post("/system/service/{svc}/{action}")
async def service_action(svc: str, action: str):
    if action not in ("start", "stop", "restart"):
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    out = subprocess.run(["systemctl", action, svc], capture_output=True, text=True, timeout=10)
    return {"success": out.returncode == 0, "service": svc, "action": action,
            "output": out.stdout + out.stderr}


@router.get("/network/status")
async def network_status():
    interfaces = []
    out = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True, timeout=3).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            iface = parts[0]
            state = parts[1]
            # PPP/tun/wg/veth etc have UNKNOWN state - map to UP if admin flags are up
            if state == "UNKNOWN":
                state = "UP"
            stats = {"name": iface, "state": state, "ip": parts[2]}
            rx = subprocess.run(f"cat /sys/class/net/{iface}/statistics/rx_bytes 2>/dev/null || echo 0",
                                shell=True, capture_output=True, text=True).stdout.strip()
            tx = subprocess.run(f"cat /sys/class/net/{iface}/statistics/tx_bytes 2>/dev/null || echo 0",
                                shell=True, capture_output=True, text=True).stdout.strip()
            stats["rx"] = int(rx) if rx.isdigit() else 0
            stats["tx"] = int(tx) if tx.isdigit() else 0
            interfaces.append(stats)
    routes = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=3).stdout.strip()
    arp = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=3).stdout.strip()
    leases = subprocess.run("cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo ''",
                            shell=True, capture_output=True, text=True, timeout=3).stdout.strip()
    firewall = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=3).stdout.strip()
    return {"interfaces": interfaces, "routes": routes, "arp": arp, "leases": leases, "firewall": firewall}


@router.get("/radius/stats")
async def radius_stats():
    from services.accel_cmd import run_accel_cmd, parse_stat
    stat = parse_stat(run_accel_cmd("show", "stat"))
    stat["radius_port_status"] = "up" if subprocess.run(
        "ss -ulnp | grep -q ':1812'", shell=True).returncode == 0 else "down"
    return {"radius": stat}


@router.get("/queues")
async def queues():
    return {"queues": []}

@router.get("/system/health/alerts")
async def system_health_alerts():
    """Check all RNAS services and return alerts for down services"""
    import subprocess, re
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
                alerts.append({"service": svc, "desc": desc, "status": out, "severity": "critical" if out == "failed" else "warning"})
        except:
            alerts.append({"service": svc, "desc": desc, "status": "unknown", "severity": "warning"})
    return {"total": len(alerts), "critical": sum(1 for a in alerts if a["severity"] == "critical"), "alerts": alerts}

@router.get("/system/notifications")
async def get_notification_config():
    """Get notification config"""
    import json, os
    path = "/etc/rnas/notifications.json"
    if os.path.exists(path):
        return json.loads(open(path).read())
    return {"telegram_bot_token": "", "telegram_chat_id": "", "webhook_url": "", "enabled": False}

@router.post("/system/notifications")
async def set_notification_config(data: dict = Body(...)):
    """Save notification config"""
    import json, os
    os.makedirs("/etc/rnas", exist_ok=True)
    with open("/etc/rnas/notifications.json", "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "saved"}

@router.post("/system/notifications/test")
async def test_notification(data: dict = Body(...)):
    """Test notification"""
    import subprocess, json
    results = []
    if data.get("telegram_bot_token") and data.get("telegram_chat_id"):
        try:
            text = "RNAS Test: System is healthy"
            r = subprocess.run(["curl", "-s", "-X", "POST",
                f"https://api.telegram.org/bot{data['telegram_bot_token']}/sendMessage",
                "-d", f"chat_id={data['telegram_chat_id']}&text={text}"],
                capture_output=True, text=True, timeout=10)
            results.append({"channel": "telegram", "ok": '"ok":true' in r.stdout})
        except:
            results.append({"channel": "telegram", "ok": False})
    if data.get("webhook_url"):
        try:
            r = subprocess.run(["curl", "-s", "-X", "POST", data["webhook_url"],
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"text": "RNAS Test: System is healthy", "event": "test"})],
                capture_output=True, text=True, timeout=10)
            results.append({"channel": "webhook", "ok": r.returncode == 0})
        except:
            results.append({"channel": "webhook", "ok": False})
    return {"results": results}
