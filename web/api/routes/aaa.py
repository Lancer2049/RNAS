"""RNAS AAA API — RADIUS users, accounting, groups, NAS clients, AIROS."""
import subprocess
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/aaa/users")
async def aaa_users():
    from rnas_env import get_env
    env = get_env()
    result = subprocess.run(
        env.db_query_str("SELECT username, attribute, value FROM radcheck ORDER BY id DESC LIMIT 50"),
        shell=True, capture_output=True, text=True, timeout=15).stdout
    users = []
    for line in result.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 3:
            users.append({"username": parts[0].strip(), "attribute": parts[1].strip(),
                          "value": parts[2].strip()})
    return {"users": users}


@router.get("/aaa/logs")
async def aaa_logs():
    return {"logs": []}


@router.get("/aaa/acct")
async def aaa_acct():
    from rnas_env import get_env
    env = get_env()
    result = subprocess.run(
        env.db_query_str("SELECT radacctid, username, nasipaddress, acctstarttime, acctstoptime, acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets, acctterminatecause FROM radacct ORDER BY radacctid DESC LIMIT 100"),
        shell=True, capture_output=True, text=True, timeout=15).stdout
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
    from rnas_env import get_env
    env = get_env()
    result = subprocess.run(
        env.db_query_str("SELECT id, username, groupname, priority FROM radusergroup ORDER BY priority, username LIMIT 100"),
        shell=True, capture_output=True, text=True, timeout=15).stdout
    groups = []
    for line in result.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            groups.append({"id": parts[0], "username": parts[1], "groupname": parts[2],
                           "priority": parts[3]})
    return {"groups": groups}


@router.get("/aaa/nas")
async def aaa_nas():
    from rnas_env import get_env
    env = get_env()
    result = subprocess.run(
        env.db_query_str("SELECT id, nasname, shortname, type, ports, secret, server FROM nas ORDER BY id"),
        shell=True, capture_output=True, text=True, timeout=15).stdout
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
    from rnas_env import get_env
    env = get_env()
    try:
        req = urllib.request.Request(f"{env.airos_url}/docs", method="GET")
        urllib.request.urlopen(req, timeout=3)
        return {"online": True, "url": env.airos_url, "freeradius_port": env.radius_auth_port}
    except Exception:
        return {"online": False, "url": env.airos_url}
