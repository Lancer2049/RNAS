"""RNAS Simulation API — subscriber dial, fault injection, scenario runner."""
import asyncio, json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


async def _run(cmd: str, **kwargs) -> subprocess.CompletedProcess | None:
    """Run a shell command in a thread pool so the event loop is not blocked."""
    import subprocess
    kwargs.setdefault("shell", True)
    kwargs.setdefault("timeout", 15)
    try:
        return await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, **kwargs)
    except Exception as e:
        print(f"[sim] _run error: {e}")


async def _ssh(cmd: str, **kwargs) -> subprocess.CompletedProcess | None:
    """SSH to a remote host. Returns None if the host is unreachable."""
    import subprocess
    kwargs.setdefault("shell", True)
    kwargs.setdefault("timeout", 10)
    try:
        return await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, **kwargs)
    except subprocess.TimeoutExpired:
        print(f"[sim] SSH timeout: {cmd[:80]}")
    except Exception as e:
        print(f"[sim] SSH error: {e}")


@router.get("/sim/connect")
async def sim_connect(
    proto: str = Query("pppoe"), user: str = Query("testuser"),
    passwd: str = Query("testpass"),
):
    from rnas_env import get_env
    env = get_env()

    if proto == "l2tp":
        await _ssh(env.ssh_cmd_str(env.cpe_host,
            "systemctl start xl2tpd 2>/dev/null; echo c rnas > /var/run/xl2tpd/l2tp-control"))
        await asyncio.sleep(8)
        out2 = await _ssh(env.ssh_cmd_str(env.cpe_host, "ip addr show dev ppp0 2>&1 | grep inet"))
        ip = out2.stdout.strip().split()[-1].split('/')[0] if out2 and 'inet' in out2.stdout else None
        return {"success": ip is not None, "ip": ip, "protocol": proto}
    else:
        peer_map = {"pppoe": "rnas-pppoe", "pptp": "rnas-pptp", "sstp": "rnas-sstp"}
        peer = peer_map.get(proto, "rnas-pppoe")
        cmd = env.ssh_cmd_str(
            env.cpe_host,
            f"timeout 12 pppd call {peer} user {user} password {passwd} nodetach 2>&1")
        out = await _ssh(cmd)
        ip = None
        if out:
            for line in out.stdout.splitlines():
                if 'local  IP address' in line:
                    ip = line.split()[-1]
                    break
            ok = 'PAP authentication succeeded' in out.stdout
        else:
            ok = False
        return {"success": ok, "ip": ip, "protocol": proto}


@router.post("/sim/stop")
async def sim_stop():
    from rnas_env import get_env
    env = get_env()
    await _ssh(env.ssh_cmd_str(env.cpe_host, "pkill pppd; pkill xl2tpd; pkill sstpc"))
    await _run("accel-cmd terminate all 2>/dev/null")
    return {"success": True}


@router.post("/sim/fault/{fault_type}")
async def fault_inject(fault_type: str):
    from rnas_env import get_env
    env = get_env()

    if fault_type == "radius-timeout":
        await _ssh(env.ssh_cmd_str(env.radius_host,
            "iptables -A INPUT -p udp --dport 1812 -j DROP"))
    elif fault_type == "radius-reject":
        return {"success": True, "info": "Use wrong password in Subscriber Sim"}
    elif fault_type == "latency":
        await _run("tc qdisc add dev ens33 root netem delay 200ms 50ms 2>/dev/null")
    elif fault_type == "packet-loss":
        await _run("tc qdisc add dev ens33 root netem loss 10% 2>/dev/null")
    elif fault_type == "clear":
        await _ssh(env.ssh_cmd_str(env.radius_host,
            "iptables -D INPUT -p udp --dport 1812 -j DROP 2>/dev/null"))
        await _run("tc qdisc del dev ens33 root 2>/dev/null")
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
