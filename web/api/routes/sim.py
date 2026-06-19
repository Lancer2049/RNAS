"""RNAS Simulation API — subscriber dial, fault injection, scenario runner."""
import subprocess, time, json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/sim/connect")
async def sim_connect(
    proto: str = Query("pppoe"), user: str = Query("testuser"),
    passwd: str = Query("testpass"),
):
    from rnas_env import get_env
    env = get_env()

    if proto == "l2tp":
        subprocess.run(
            env.ssh_cmd_str(env.cpe_host,
                "systemctl start xl2tpd 2>/dev/null; sleep 4; echo c rnas > /var/run/xl2tpd/l2tp-control"),
            shell=True, timeout=15)
        time.sleep(8)
        out2 = subprocess.run(
            env.ssh_cmd_str(env.cpe_host, "ip addr show dev ppp0 2>&1 | grep inet"),
            shell=True, capture_output=True, text=True, timeout=10)
        ip = out2.stdout.strip().split()[-1].split('/')[0] if 'inet' in out2.stdout else None
        return {"success": ip is not None, "ip": ip, "protocol": proto}
    else:
        peer_map = {"pppoe": "rnas-pppoe", "pptp": "rnas-pptp", "sstp": "rnas-sstp"}
        peer = peer_map.get(proto, "rnas-pppoe")
        cmd = env.ssh_cmd_str(
            env.cpe_host,
            f"timeout 12 pppd call {peer} user {user} password {passwd} nodetach 2>&1")
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        ip = None
        for line in out.stdout.splitlines():
            if 'local  IP address' in line:
                ip = line.split()[-1]
                break
        ok = 'PAP authentication succeeded' in out.stdout
        return {"success": ok, "ip": ip, "protocol": proto}


@router.post("/sim/stop")
async def sim_stop():
    from rnas_env import get_env
    env = get_env()
    subprocess.run(env.ssh_cmd_str(env.cpe_host, "pkill pppd; pkill xl2tpd; pkill sstpc"),
                   shell=True, timeout=10)
    subprocess.run("accel-cmd terminate all 2>/dev/null", shell=True, timeout=5)
    return {"success": True}


@router.post("/sim/fault/{fault_type}")
async def fault_inject(fault_type: str):
    from rnas_env import get_env
    env = get_env()

    if fault_type == "radius-timeout":
        subprocess.run(env.ssh_cmd_str(env.radius_host,
            "iptables -A INPUT -p udp --dport 1812 -j DROP"), shell=True, timeout=10)
    elif fault_type == "radius-reject":
        return {"success": True, "info": "Use wrong password in Subscriber Sim"}
    elif fault_type == "latency":
        subprocess.run("tc qdisc add dev ens33 root netem delay 200ms 50ms 2>/dev/null",
                       shell=True, timeout=5)
    elif fault_type == "packet-loss":
        subprocess.run("tc qdisc add dev ens33 root netem loss 10% 2>/dev/null",
                       shell=True, timeout=5)
    elif fault_type == "clear":
        subprocess.run(env.ssh_cmd_str(env.radius_host,
            "iptables -D INPUT -p udp --dport 1812 -j DROP 2>/dev/null"), shell=True, timeout=10)
        subprocess.run("tc qdisc del dev ens33 root 2>/dev/null", shell=True, timeout=5)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown fault: {fault_type}")
    return {"success": True}


# ── Scenario Runner ──

@router.get("/scenarios")
async def list_scenarios():
    from rnas_config import walk_config_tree, write_config_section
    scenario_dir = Path("/etc/rnas/scenarios")
    scenario_dir.mkdir(parents=True, exist_ok=True)
    scenarios = []
    for f in sorted(scenario_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            scenarios.append({
                "id": f.stem, "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "sections": len(data.get("config", {})),
            })
        except Exception:
            pass
    return {"scenarios": scenarios}


@router.post("/scenarios/{scenario_id}/load")
async def load_scenario(scenario_id: str):
    from rnas_config import write_config_section
    scenario_file = Path(f"/etc/rnas/scenarios/{scenario_id}.json")
    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    data = json.loads(scenario_file.read_text())
    imported = data.get("config", {})
    applied = 0
    for section_name, values in imported.items():
        section = section_name.rsplit(".", 1)[-1] if "." in section_name else section_name
        if write_config_section(Path("/etc/rnas"), section, values):
            applied += 1
    return {"success": True, "scenario": data.get("name", scenario_id),
            "applied": applied, "total": len(imported)}
