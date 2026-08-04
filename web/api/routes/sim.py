"""RNAS Simulation API — subscriber dial, fault injection, scenario runner."""
import asyncio, json, re, shlex, subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from api.auth import require_auth
from api.models import MultiConnectRequest

router = APIRouter(tags=["Simulation"])


async def _run(cmd: str, **kwargs) -> subprocess.CompletedProcess | None:
    """Run a shell command in a thread pool so the event loop is not blocked."""
    kwargs.setdefault("shell", True)
    kwargs.setdefault("timeout", 15)
    try:
        return await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, **kwargs)
    except Exception as e:
        print(f"[sim] _run error: {e}")


async def _ssh(cmd: str, **kwargs) -> subprocess.CompletedProcess | None:
    """SSH to a remote host. Returns None if the host is unreachable."""
    kwargs.setdefault("shell", True)
    kwargs.setdefault("timeout", 10)
    try:
        return await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, **kwargs)
    except subprocess.TimeoutExpired:
        print(f"[sim] SSH timeout: {cmd[:80]}")
    except Exception as e:
        print(f"[sim] SSH error: {e}")


async def _dial_one(proto: str, user: str, passwd: str) -> dict:
    """Dial a single subscriber connection. Shared by single and multi-user paths."""
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
        # shlex.quote: user/passwd are URL params — prevent shell injection
        # into the remote pppd command.
        safe_user = shlex.quote(user)
        safe_pass = shlex.quote(passwd)
        cmd = env.ssh_cmd_str(
            env.cpe_host,
            f"timeout 12 pppd call {peer} user {safe_user} password {safe_pass} nodetach 2>&1")
        # The remote pppd runs for up to 12s before `timeout` SIGTERMs it —
        # the SSH call needs a larger timeout than _ssh's 10s default.
        out = await _ssh(cmd, timeout=15)
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


@router.get("/sim/connect")
async def sim_connect(
    proto: str = Query("pppoe"), user: str = Query("testuser"),
    passwd: str = Query("testpass"), _auth=Depends(require_auth),
):
    return await _dial_one(proto, user, passwd)


@router.post("/sim/multi-connect")
async def sim_multi_connect(data: MultiConnectRequest = Body(...), _auth=Depends(require_auth)):
    """Batch-dial N subscribers with auto-created RADIUS users.

    Creates users <base>-1..<base>-N in radcheck (Cleartext-Password),
    dials each serially, then removes them so the DB stays clean.
    """
    from rnas_env import get_env
    env = get_env()

    proto = data.proto
    base_user = data.user
    passwd = data.password
    count = data.count
    if proto == "l2tp":
        raise HTTPException(status_code=400, detail="l2tp is a single tunnel; use /sim/connect")

    users = [f"{base_user}-{i}" for i in range(1, count + 1)]
    esc_p = passwd.replace("'", "''")

    created = []
    try:
        # 1. Create RADIUS users (idempotent: delete-then-insert)
        for u in users:
            esc_u = u.replace("'", "''")
            env.db_exec(
                f"DELETE FROM radcheck WHERE username='{esc_u}';"
                f"INSERT INTO radcheck (username, attribute, op, value) "
                f"VALUES ('{esc_u}', 'Cleartext-Password', ':=', '{esc_p}');"
            )
            created.append(u)

        # 2. Dial serially — CPE pppd is one tunnel per call
        results = []
        for u in users:
            r = await _dial_one(proto, u, passwd)
            results.append({"username": u, **r})
    finally:
        # 3. Always clean up created users, even on dial/DB failure
        for u in created:
            env.db_exec(f"DELETE FROM radcheck WHERE username='{u.replace(chr(39), chr(39)*2)}'")

    return {"success": True, "count": count, "results": results}


@router.post("/sim/stop")
async def sim_stop(user=Depends(require_auth)):
    from rnas_env import get_env
    env = get_env()
    await _ssh(env.ssh_cmd_str(env.cpe_host, "pkill pppd; pkill xl2tpd; pkill sstpc"))
    await _run("accel-cmd terminate all 2>/dev/null")
    return {"success": True}


@router.post("/sim/fault/{fault_type}")
async def fault_inject(fault_type: str, user=Depends(require_auth)):
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
async def list_scenarios(user=Depends(require_auth)):
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
async def load_scenario(scenario_id: str, user=Depends(require_auth)):
    from rnas_config import write_config_section
    # Prevent path traversal: only allow [a-z0-9-] in scenario id
    if not re.match(r"^[a-z0-9-]+$", scenario_id):
        raise HTTPException(status_code=400, detail="Invalid scenario id")
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
