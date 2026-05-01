#!/usr/bin/env python3
"""RNAS Web Server — serves API + static frontend using only stdlib."""
import json, os, re, subprocess, sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from rnas_config import write_config_section

STATIC_DIR = Path(__file__).parent / "static"
API_ONLY = False


def run_accel_cmd(*args):
    try:
        return subprocess.run(["/usr/bin/accel-cmd"] + list(args),
                              capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def parse_sessions(raw):
    rows = []
    body = False
    for line in raw.splitlines():
        if not body:
            if line.strip().startswith("ifname") or line.strip().startswith("---"):
                body = True
            continue
        cols = line.split()
        if len(cols) >= 9:
            rows.append(dict(sid=cols[0], ifname=cols[1], username=cols[2],
                             ip=cols[3], type=cols[4], state=cols[5],
                             uptime_raw=cols[6], rx_bytes_raw=int(cols[7]) if cols[7].isdigit() else 0,
                             tx_bytes_raw=int(cols[8]) if cols[8].isdigit() else 0))
    return rows


def parse_stat(raw):
    stat = dict(uptime="N/A", cpu="0%", mem="N/A", sessions_active=0, radius_state="unknown",
                radius_fail_count=0, auth_sent=0, acct_sent=0)
    for key, pat in [("uptime", r"uptime:\s*(\S+)"), ("cpu", r"cpu:\s*(\S+)"),
                     ("mem", r"mem\(rss/virt\):\s*(\S+)"),
                     ("sessions_active", r"sessions:.*?active:\s*(\d+)"),
                     ("radius_state", r"state:\s*(\S+)"),
                     ("radius_fail_count", r"fail count:\s*(\d+)"),
                     ("auth_sent", r"auth sent:\s*(\d+)"),
                     ("acct_sent", r"acct sent:\s*(\d+)")]:
        m = re.search(pat, raw, re.DOTALL)
        if m:
            val = m.group(1)
            stat[key] = int(val) if val.isdigit() else val
    return stat


class RNASHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self.handle_api(path)
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self.handle_api(path)
        else:
            self.send_error(404)

    def do_PUT(self):
        path = urlparse(self.path).path
        if path.startswith("/api/config/"):
            self.handle_config_put(path)
        else:
            self.send_error(404)

    def handle_config_put(self, path):
        content_len = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_len))
        module = path.replace("/api/config/", "").replace("/", ".")
        section_name = module.rsplit(".", 1)[-1] if "." in module else module
        root = Path("/etc/rnas")
        success = write_config_section(root, section_name, body)
        if success:
            self.json(dict(success=True, module=module, updated=body))
        else:
            self.send_error(404, "Section not found")

    def handle_api(self, path):
        if path == "/api/health":
            self.json(dict(status="ok", version="2.0.0"))
        elif path == "/api/status":
            raw_stat = run_accel_cmd("show", "stat")
            raw_sess = run_accel_cmd("show", "sessions",
                                     "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw")
            sessions = parse_sessions(raw_sess)
            self.json(dict(service=parse_stat(raw_stat), sessions=sessions, sessions_count=len(sessions)))
        elif path == "/api/sessions":
            raw = run_accel_cmd("show", "sessions",
                                "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw")
            self.json(parse_sessions(raw))
        elif path.startswith("/api/sessions/") and path.endswith("/disconnect"):
            sid = path.split("/")[3]
            out = run_accel_cmd("terminate", "sid", sid, "hard")
            self.json(dict(success=True, message=f"Session {sid} terminated"))
        elif path == "/api/tools/ping":
            qs = parse_qs(urlparse(self.path).query)
            host = qs.get("host", ["8.8.8.8"])[0]
            out = subprocess.run(["ping", "-c", "3", "-W", "2", host],
                                 capture_output=True, text=True, timeout=10).stdout
            self.json(dict(output=out))
        elif path == "/api/tools/trace":
            qs = parse_qs(urlparse(self.path).query)
            host = qs.get("host", ["8.8.8.8"])[0]
            out = subprocess.run(["traceroute", "-m", "10", host],
                                 capture_output=True, text=True, timeout=15).stdout
            self.json(dict(output=out))
        elif path == "/api/tools/radius-test":
            qs = parse_qs(urlparse(self.path).query)
            user, passwd = qs.get("user", ["testuser"])[0], qs.get("pass", ["testpass"])[0]
            out = subprocess.run(
                f"echo '{passwd}' | radclient -r 1 -t 3 192.168.0.202:1812 auth testing123 <<< 'User-Name={user}'",
                shell=True, capture_output=True, text=True, timeout=10).stdout
            self.json(dict(output=out))
        elif path == "/api/tools/coa":
            qs = parse_qs(urlparse(self.path).query)
            user = qs.get("user", [""])[0]
            out = subprocess.run(
                f"echo 'User-Name={user}' | radclient -r 1 -t 5 127.0.0.1:3799 disconnect testing123",
                shell=True, capture_output=True, text=True, timeout=10).stdout
            self.json(dict(output=out))
        elif path == "/api/system/status":
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
                except:
                    active = "unknown"
                svcs.append(dict(name=name, active=active, desc=desc))
            mem = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.splitlines()[1]
            disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.splitlines()[1]
            self.json(dict(services=svcs, memory=mem.split()[1] + "/" + mem.split()[0], disk=disk.split()[2] + "/" + disk.split()[1]))
        elif path == "/api/system/logs":
            try:
                out = subprocess.run(["journalctl", "-u", "rnas-accel-ppp", "--no-pager", "-n", "30"],
                                     capture_output=True, text=True, timeout=5).stdout
            except:
                out = "Logs unavailable"
            self.json(dict(logs=out))
        elif path == "/api/config/apply":
            for svc, sub in [("accel-ppp", "accel-ppp"), ("dnsmasq", "dnsmasq"), ("firewall", "firewall"), ("snmp", "snmp")]:
                subprocess.run(["python3", "/usr/bin/rnas-config", "--root", "/etc/rnas",
                                "generate", sub, "-o", f"/var/run/rnas/{sub}.conf"],
                               capture_output=True, timeout=5)
            subprocess.run(["systemctl", "reload-or-restart", "rnas-accel-ppp", "rnas-dnsmasq"], capture_output=True, timeout=10)
            self.json(dict(success=True, message="Configuration applied"))
        else:
            self.send_error(404)

    def json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[rnas-web] {args[0]}", flush=True)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    print(f"RNAS Web Server on http://0.0.0.0:{port}")
    HTTPServer(("0.0.0.0", port), RNASHandler).serve_forever()
