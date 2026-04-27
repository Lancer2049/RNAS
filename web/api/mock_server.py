from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

app = FastAPI(title="RNAS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_state = {
    "config": {
        "network.d.interface/lan": {"device": "br-lan", "proto": "static", "ipaddr": "192.168.100.1", "netmask": "255.255.255.0"},
        "network.d.dhcp/dhcp lan": {"start": "100", "limit": "100", "leasetime": "12h"},
        "network.d.dhcp/dhcp_option dns": {"list": "8.8.8.8,8.8.4.4"},
        "network.d.zone/nas": {"input": "ACCEPT", "output": "ACCEPT", "forward": "REJECT", "networks": "lan"},
        "network.d.device/br-lan": {"type": "bridge", "ports": "ens33"},
        "access.d.server/primary": {"auth_host": "192.168.0.85", "auth_port": "1812", "secret": "testing123"},
        "access.d.pppoe": {"interface": "ens33", "ac_name": "RNAS"},
        "qos.global": {"enabled": "no", "algorithm": "cake", "interface": "ens33"},
        "vpn.d.ipsec.global": {"enabled": "no", "auth": "radius"},
        "hotspot.global": {"enabled": "no", "interface": "br-lan"},
        "ha.global": {"enabled": "no"},
    }
}

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/status")
async def status():
    return {
        "service": {"uptime": "0.00:01:23", "cpu": "2%", "mem": "5648/250488 kB",
                    "sessions_active": 3, "radius_state": "active",
                    "radius_fail_count": 0, "auth_sent": 127, "acct_sent": 89},
        "sessions": [
            {"sid": "abc123", "ifname": "ppp0", "username": "testuser",
             "ip": "192.168.100.10", "type": "pppoe", "state": "active",
             "uptime_raw": "3600", "rx_bytes_raw": 1048576, "tx_bytes_raw": 524288},
            {"sid": "def456", "ifname": "ppp1", "username": "user2",
             "ip": "192.168.100.11", "type": "pppoe", "state": "active",
             "uptime_raw": "1800", "rx_bytes_raw": 512000, "tx_bytes_raw": 256000}
        ],
        "sessions_count": 2
    }

@app.get("/api/sessions")
async def sessions():
    return [
        {"sid": "abc123", "ifname": "ppp0", "username": "testuser",
         "ip": "192.168.100.10", "type": "pppoe", "state": "active",
         "uptime_raw": "3600", "rx_bytes_raw": 1048576, "tx_bytes_raw": 524288}
    ]

@app.get("/api/config")
async def config():
    return {"config": _state["config"]}

@app.put("/api/config/{module:path}")
async def update_config(module: str, values: Dict[str, str] = Body(...)):
    key = module.replace("/", ".")
    if key in _state["config"]:
        _state["config"][key].update(values)
    else:
        _state["config"][key] = values
    return {"success": True, "module": module, "updated": values}

@app.post("/api/config/apply")
async def apply_config():
    return {"success": True, "message": "Configuration applied"}

@app.post("/api/sessions/{sid}/disconnect")
async def disconnect(sid: str):
    return {"success": True, "message": f"Session {sid} terminated"}
