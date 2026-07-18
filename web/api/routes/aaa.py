"""RNAS AAA API — RADIUS users, accounting, groups, NAS clients, AIROS."""
from pathlib import Path
from fastapi import APIRouter
from rnas_env import get_env

router = APIRouter(tags=["AAA RADIUS"])


@router.get("/aaa/users")
async def aaa_users():
    users = []
    # Try RADIUS user files first
    for fp in ["/etc/freeradius/3.0/mods-config/files/authorize", "/etc/freeradius/users"]:
        p = Path(fp)
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("DEFAULT"):
                continue
            parts = line.split(None, 3)
            if len(parts) >= 3:
                users.append({"username": parts[0], "attribute": parts[1].rstrip(","), "value": parts[3].strip(chr(34)) if len(parts)>3 else ""})
        if users:
            break
    # Fallback to SQL
    if not users:
        env = get_env()
        result = env.db_query("SELECT username, attribute, value FROM radcheck ORDER BY id DESC LIMIT 50")
        for line in result.splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 3:
                users.append({"username": parts[0].strip(), "attribute": parts[1].strip(), "value": parts[2].strip()})
    return {"users": users, "count": len(users)}


@router.get("/aaa/logs")
async def aaa_logs():
    return {"logs": []}


@router.get("/aaa/acct")
async def aaa_acct():
    env = get_env()
    result = env.db_query(
        "SELECT radacctid, username, nasipaddress, acctstarttime, acctstoptime, "
        "acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets, "
        "acctterminatecause FROM radacct ORDER BY radacctid DESC LIMIT 100"
    )
    records = []
    for line in result.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 10:
            records.append({"id": parts[0], "username": parts[1], "nas": parts[2],
                            "start": parts[3], "stop": parts[4], "duration": parts[5],
                            "ip": parts[6], "rx": parts[7], "tx": parts[8], "cause": parts[9]})
    return {"records": records}


@router.get("/aaa/groups")
async def aaa_groups():
    env = get_env()
    result = env.db_query(
        "SELECT id, username, groupname, priority FROM radusergroup ORDER BY priority, username LIMIT 100"
    )
    groups = []
    for line in result.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            groups.append({"id": parts[0], "username": parts[1], "groupname": parts[2],
                           "priority": parts[3]})
    return {"groups": groups}


@router.get("/aaa/nas")
async def aaa_nas():
    env = get_env()
    result = env.db_query(
        "SELECT id, nasname, shortname, type, ports, secret, server FROM nas ORDER BY id"
    )
    nas_list = []
    for line in result.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7:
            nas_list.append({"id": parts[0], "nasname": parts[1], "shortname": parts[2],
                             "type": parts[3], "ports": parts[4], "secret": parts[5],
                             "server": parts[6]})
    return {"nas": nas_list}


@router.get("/airos/status")
async def airos_status():
    import urllib.request
    env = get_env()
    try:
        req = urllib.request.Request(f"{env.airos_url}/docs", method="GET")
        urllib.request.urlopen(req, timeout=3)
        return {"online": True, "url": env.airos_url, "freeradius_port": env.radius_auth_port}
    except Exception:
        return {"online": False, "url": env.airos_url}
