"""RNAS System API — systemd services, logs, network interfaces, SNMP queues."""
import subprocess
from fastapi import APIRouter, HTTPException

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
    return {
        "services": svcs,
        "memory": f"{mem[2]}/{mem[1]}" if len(mem) >= 3 else "N/A",
        "disk": f"{disk[2]}/{disk[1]}" if len(disk) >= 3 else "N/A",
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
            stats = {"name": iface, "state": parts[1], "ip": parts[2]}
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
