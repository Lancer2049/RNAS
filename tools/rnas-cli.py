#!/usr/bin/env python3
"""
RNAS CLI Diagnostics Tool
Usage:
  rnas-cli status              Show system status
  rnas-cli sessions            List active sessions
  rnas-cli session <sid>       Show session details
  rnas-cli disconnect <sid>    Disconnect a session
  rnas-cli coa <username>      Send CoA disconnect
  rnas-cli radius-test <user>  Test RADIUS authentication
  rnas-cli interfaces          List network interfaces
  rnas-cli logs [service]      View service logs
"""

import sys
import json
import subprocess
import urllib.request

API = "http://127.0.0.1:8099"

def api_get(path):
    try:
        resp = urllib.request.urlopen(f"{API}{path}", timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def api_post(path, data=None):
    try:
        body = json.dumps(data).encode() if data else b""
        req = urllib.request.Request(f"{API}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def cmd_status():
    d = api_get("/api/status")
    svc = d.get("service", {})
    print(f"Uptime:   {svc.get('uptime')}")
    print(f"CPU:      {svc.get('cpu')}")
    print(f"Memory:   {svc.get('mem')}")
    print(f"RADIUS:   {svc.get('radius_state')}")
    print(f"Auth:     {svc.get('auth_sent')} sent")
    print(f"Acct:     {svc.get('acct_sent')} sent")
    print(f"Sessions: {d.get('sessions_count', 0)} active")

def cmd_sessions():
    d = api_get("/api/status")
    for s in d.get("sessions", []):
        print(f"  {s['sid'][:12]}  {s['username']:12s} {s['ip']:16s} {s['type']:6s} {s['state']}")
    if not d.get("sessions"):
        print("  No active sessions")

def cmd_session(sid):
    d = api_get("/api/status")
    for s in d.get("sessions", []):
        if s["sid"].startswith(sid):
            for k, v in s.items():
                print(f"  {k}: {v}")
            return
    print(f"Session '{sid}' not found")

def cmd_disconnect(sid):
    r = api_post(f"/api/sessions/{sid}/disconnect")
    print(r.get("message", "Disconnected"))

def cmd_coa(username):
    r = api_get(f"/api/tools/coa?user={username}")
    print(r.get("output", "CoA sent"))

def cmd_radius_test(username="testuser", password="testpass"):
    r = api_get(f"/api/tools/radius-test?user={username}&pass={password}")
    out = r.get("output", "")
    if "Access-Accept" in out:
        print(f"✅ {username}: Access-Accept")
    elif "Access-Reject" in out:
        print(f"❌ {username}: Access-Reject")
    else:
        print(f"  {out[:80]}")

def cmd_interfaces():
    d = api_get("/api/interfaces")
    for i in d.get("interfaces", []):
        print(f"  {i['name']:8s} {'UP' if i['running'] else 'DOWN':5s} "
              f"rx={i['rx_bytes']//1024}KB tx={i['tx_bytes']//1024}KB")

def cmd_logs(service="rnas-accel-ppp"):
    lines = 30
    d = api_get(f"/api/system/log?lines={lines}&unit={service}.service")
    print(d.get("log", "No logs")[:2000])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    cmds = {
        "status": cmd_status,
        "sessions": cmd_sessions,
        "disconnect": lambda: cmd_disconnect(args[0]) if args else print("Usage: rnas-cli disconnect <sid>"),
        "coa": lambda: cmd_coa(args[0]) if args else print("Usage: rnas-cli coa <username>"),
        "radius-test": lambda: cmd_radius_test(args[0] if args else "testuser"),
        "interfaces": cmd_interfaces,
        "logs": lambda: cmd_logs(args[0] if args else "rnas-accel-ppp"),
    }

    if cmd in cmds:
        cmds[cmd]()
    elif cmd == "session" and args:
        cmd_session(args[0])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
