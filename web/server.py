#!/usr/bin/env python3
"""RNAS Web Server — serves API + static frontend using only stdlib."""
import json, os, re, subprocess, sys, time, hashlib, base64, struct, threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from rnas_config import write_config_section, walk_config_tree
from rnas_dict.dictionary import load_all, search as dict_search
from rnas_env import get_env
from rnas_env import get_env

_env = get_env()

DICT_DIR = _env.dict_dir
STATIC_DIR = _env.static_dir
API_ONLY = False


def run_accel_cmd(*args):
    try:
        return subprocess.run([_env.accel_cmd_bin] + list(args),
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
        if path == "/api/ws":
            self.handle_websocket()
        elif path.startswith("/hotspot"):
            self.path = "/hotspot/login.html"
            super().do_GET()
        elif path.startswith("/api/"):
            self.handle_api(path)
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/hotspot/login":
            self._handle_hotspot_login()
        elif path.startswith("/api/"):
            self.handle_api(path)
        else:
            self.send_error(404)

    def _handle_hotspot_login(self):
        cl = int(self.headers.get("Content-Length", 0))
        body = parse_qs(self.rfile.read(cl).decode())
        user, pwd = body.get("username", [""])[0], body.get("password", [""])[0]
        if not user:
            self.send_error(400); return
        payload = f"User-Name={user},User-Password={pwd}"
        from rnas_env import get_env
        env = get_env()
        result = subprocess.run(
            ["radclient", "-r", "1", "-t", "3", f"{env.radius_host}:{env.radius_auth_port}",
             "auth", env.radius_secret],
            input=payload, capture_output=True, text=True, timeout=10)
        ok = "Access-Accept" in result.stdout
        self.send_response(302 if ok else 403)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"Authenticated" if ok else b"Access Denied")

    def do_PUT(self):
        path = urlparse(self.path).path
        if path.startswith("/api/config/"):
            self.handle_config_put(path)
        else:
            self.send_error(404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/config/snapshot/"):
            self.command = "DELETE"
            self.handle_api(path)

    def handle_websocket(self):
        key = self.headers.get("Sec-WebSocket-Key", "")
        if not key:
            self.send_error(400)
            return
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        while True:
            try:
                raw_stat = run_accel_cmd("show", "stat")
                raw_sess = run_accel_cmd("show", "sessions", "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw")
                msg = json.dumps({"service": parse_stat(raw_stat), "sessions": parse_sessions(raw_sess)})
                frame = b'\x81' + bytes([min(len(msg), 125)]) + msg.encode()
                self.wfile.write(frame)
                time.sleep(3)
            except:
                break

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
            attrs = qs.get("attrs", [""])[0]
            attr_pairs = [f"User-Name={user},User-Password={passwd}"]
            if attrs:
                attr_pairs.append(attrs)
            payload = ",".join(attr_pairs)
            out = subprocess.run(
                ["radclient", "-r", "1", "-t", "3", f"{_env.radius_host}:{_env.radius_auth_port}", "auth", _env.radius_secret],
                input=payload, capture_output=True, text=True, timeout=10).stdout + "\n" + \
                subprocess.run(
                ["radclient", "-r", "1", "-t", "3", f"{_env.radius_host}:{_env.radius_auth_port}", "auth", _env.radius_secret],
                input=payload, capture_output=True, text=True, timeout=10).stderr
            self.json(dict(output=out.strip(), payload=payload))
        elif path == "/api/tools/radius-send":
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len))
            server = data.get("server", f"{_env.radius_host}:{_env.radius_auth_port}")
            secret = data.get("secret", _env.radius_secret)
            port_type = data.get("type", "auth")
            attributes = data.get("attributes", [])
            pairs = [f"{a['name']}={a['value']}" for a in attributes if a.get('name') and a.get('value')]
            payload = ",".join(pairs)
            result = subprocess.run(
                ["radclient", "-r", "1", "-t", "3", server, port_type, secret],
                input=payload, capture_output=True, text=True, timeout=10)
            self.json(dict(success=True, output=result.stdout + "\n" + result.stderr, payload=payload, code=result.returncode))
        elif path == "/api/tools/coa":
            qs = parse_qs(urlparse(self.path).query)
            user = qs.get("user", [""])[0]
            out = subprocess.run(
                f"echo 'User-Name={user}' | radclient -r 1 -t 5 127.0.0.1:{_env.radius_coa_port} disconnect {_env.radius_secret}",
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
        elif path == "/api/network/status":
            interfaces = []
            out = subprocess.run(["ip", "-br", "addr"], capture_output=True, text=True, timeout=3).stdout
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    iface = parts[0]
                    stats = {"name": iface, "state": parts[1], "ip": parts[2]}
                    rx = subprocess.run(f"cat /sys/class/net/{iface}/statistics/rx_bytes 2>/dev/null || echo 0", shell=True, capture_output=True, text=True).stdout.strip()
                    tx = subprocess.run(f"cat /sys/class/net/{iface}/statistics/tx_bytes 2>/dev/null || echo 0", shell=True, capture_output=True, text=True).stdout.strip()
                    stats["rx"] = int(rx) if rx.isdigit() else 0
                    stats["tx"] = int(tx) if tx.isdigit() else 0
                    interfaces.append(stats)
            routes = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=3).stdout.strip()
            arp = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=3).stdout.strip()
            leases = subprocess.run("cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo ''", shell=True, capture_output=True, text=True, timeout=3).stdout.strip()
            firewall = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=3).stdout.strip()
            self.json(dict(interfaces=interfaces, routes=routes, arp=arp, leases=leases, firewall=firewall))
        elif path == "/api/aaa/users":
            result = subprocess.run(
                _env.db_query("SELECT username, attribute, value FROM radcheck ORDER BY id DESC LIMIT 50"),
                capture_output=True, text=True, timeout=15).stdout
            users = []
            for line in result.splitlines():
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    users.append({"username": parts[0].strip(), "attribute": parts[1].strip(), "value": parts[2].strip()})
            self.json(dict(users=users))
        elif path == "/api/aaa/logs":
            self.json(dict(logs=[]))
        elif path == "/api/radius/stats":
            raw = run_accel_cmd("show", "stat")
            stat = parse_stat(raw)
            stat["radius_port_status"] = "up" if subprocess.run("ss -ulnp | grep -q ':1812'", shell=True).returncode == 0 else "down"
            self.json(dict(radius=stat))
        elif path == "/api/queues":
            self.json(dict(queues=[]))
        elif path == "/api/sniffer/start":
            subprocess.run("pkill tcpdump 2>/dev/null", shell=True)
            subprocess.run("nohup tcpdump -i any -w /tmp/rnas-sniffer.pcap udp port 1812 or udp port 1813 or udp port 3799 &", shell=True, timeout=5)
            self.json(dict(success=True, message="Sniffer started"))
        elif path == "/api/sniffer/stop":
            subprocess.run("pkill tcpdump 2>/dev/null", shell=True, timeout=5)
            self.json(dict(success=True, message="Sniffer stopped"))
        elif path == "/api/sniffer/status":
            running = subprocess.run("pgrep -f 'tcpdump.*rnas-sniffer'", shell=True, capture_output=True).returncode == 0
            size = 0
            try: size = os.path.getsize("/tmp/rnas-sniffer.pcap")
            except: pass
            self.json(dict(running=running, size=size))
        elif path == "/api/scheduler":
            self.json(dict(tasks=[]))
        elif path == "/api/sim/connect":
            qs = parse_qs(urlparse(self.path).query)
            proto = qs.get("proto", ["pppoe"])[0]
            user = qs.get("user", ["testuser"])[0]
            passwd = qs.get("pass", ["testpass"])[0]
            if proto == "l2tp":
                subprocess.run(_env.ssh_cmd(_env.cpe_host,
                    'systemctl start xl2tpd 2>/dev/null; sleep 4; echo c rnas > /var/run/xl2tpd/l2tp-control'), timeout=15)
                time.sleep(8)
                out2 = subprocess.run(_env.ssh_cmd(_env.cpe_host,
                    'ip addr show dev ppp0 2>&1 | grep inet'), capture_output=True, text=True, timeout=10)
                ip = out2.stdout.strip().split()[-1].split('/')[0] if 'inet' in out2.stdout else None
                self.json(dict(success=ip is not None, ip=ip, protocol=proto))
            else:
                peer_map = {"pppoe":"rnas-pppoe","pptp":"rnas-pptp","sstp":"rnas-sstp"}
                peer = peer_map.get(proto, "rnas-pppoe")
                cmd = _env.ssh_cmd(_env.cpe_host,
                    f"timeout 12 pppd call {peer} user {user} password {passwd} nodetach 2>&1")
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                ip = None
                for line in out.stdout.splitlines():
                    if 'local  IP address' in line:
                        ip = line.split()[-1]
                        break
                ok = 'PAP authentication succeeded' in out.stdout
                self.json(dict(success=ok, ip=ip, protocol=proto))
        elif path == "/api/sim/stop":
            subprocess.run(_env.ssh_cmd(_env.cpe_host,
                'pkill pppd; pkill xl2tpd; pkill sstpc'), timeout=10)
            subprocess.run(_env.ssh_cmd(_env.cpe_host, 'accel-cmd terminate all 2>/dev/null'), timeout=5)
            self.json(dict(success=True))
        elif path == "/api/sim/fault/radius-timeout":
            subprocess.run(_env.ssh_cmd(_env.radius_host,
                'iptables -A INPUT -p udp --dport 1812 -j DROP'), timeout=10)
            self.json(dict(success=True))
        elif path == "/api/sim/fault/radius-reject":
            self.json(dict(success=True, info="Use wrong password in Subscriber Sim"))
        elif path == "/api/sim/fault/latency":
            subprocess.run("tc qdisc add dev ens33 root netem delay 200ms 50ms 2>/dev/null", shell=True, timeout=5)
            self.json(dict(success=True))
        elif path == "/api/sim/fault/packet-loss":
            subprocess.run("tc qdisc add dev ens33 root netem loss 10% 2>/dev/null", shell=True, timeout=5)
            self.json(dict(success=True))
        elif path == "/api/sim/fault/clear":
            subprocess.run(_env.ssh_cmd(_env.radius_host,
                'iptables -D INPUT -p udp --dport 1812 -j DROP 2>/dev/null'), timeout=10)
            subprocess.run("tc qdisc del dev ens33 root 2>/dev/null", shell=True, timeout=5)
            self.json(dict(success=True))
        elif path == "/api/aaa/acct":
            result = subprocess.run(
                _env.db_query_str("SELECT radacctid, username, nasipaddress, acctstarttime, acctstoptime, acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets, acctterminatecause FROM radacct ORDER BY radacctid DESC LIMIT 100"),
                shell=True, capture_output=True, text=True, timeout=15).stdout
            records = []
            for line in result.splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 10:
                    records.append({"id":parts[0],"username":parts[1],"nas":parts[2],"start":parts[3],"stop":parts[4],"duration":parts[5],"ip":parts[6],"rx":parts[7],"tx":parts[8],"cause":parts[9]})
            self.json(dict(records=records))
        elif path == "/api/aaa/groups":
            result = subprocess.run(
                _env.db_query_str("SELECT id, username, groupname, priority FROM radusergroup ORDER BY priority, username LIMIT 100"),
                shell=True, capture_output=True, text=True, timeout=15).stdout
            groups = []
            for line in result.splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    groups.append({"id":parts[0],"username":parts[1],"groupname":parts[2],"priority":parts[3]})
            self.json(dict(groups=groups))
        elif path == "/api/aaa/nas":
            result = subprocess.run(
                _env.db_query_str("SELECT id, nasname, shortname, type, ports, secret, server FROM nas ORDER BY id"),
                shell=True, capture_output=True, text=True, timeout=15).stdout
            nas_list = []
            for line in result.splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 7:
                    nas_list.append({"id":parts[0],"nasname":parts[1],"shortname":parts[2],"type":parts[3],"ports":parts[4],"secret":parts[5],"server":parts[6]})
            self.json(dict(nas=nas_list))
        elif path.startswith("/api/system/service/"):
            parts = path.split("/")
            svc = parts[4] if len(parts) > 4 else ""
            action = parts[5] if len(parts) > 5 else "status"
            if svc and action in ("start", "stop", "restart"):
                out = subprocess.run(["systemctl", action, svc], capture_output=True, text=True, timeout=10)
                self.json(dict(success=out.returncode==0, service=svc, action=action, output=out.stdout+out.stderr))
            else:
                self.json(dict(success=False, error="Invalid service or action"))
        elif path == "/api/airos/status":
            import urllib.request
            try:
                req = urllib.request.Request(f"{_env.airos_url}/docs", method="GET")
                urllib.request.urlopen(req, timeout=3)
                self.json(dict(online=True, url=_env.airos_url, freeradius_port=_env.radius_auth_port))
            except:
                self.json(dict(online=False, url=_env.airos_url))
        elif path == "/api/config":
            config = walk_config_tree(Path("/etc/rnas"))
            self.json(dict(success=True, config=config))
        elif path == "/api/scenarios":
            scenario_dir = Path("/etc/rnas/scenarios")
            scenario_dir.mkdir(parents=True, exist_ok=True)
            scenarios = []
            for f in sorted(scenario_dir.glob("*.json")):
                try:
                    data = json.loads(f.read_text())
                    scenarios.append({"id": f.stem, "name": data.get("name", f.stem), "description": data.get("description", ""), "sections": len(data.get("config", {}))})
                except:
                    pass
            self.json(dict(scenarios=scenarios))
        elif path.startswith("/api/scenarios/") and path.endswith("/load"):
            scenario_id = path.split("/")[3]
            scenario_file = Path(f"/etc/rnas/scenarios/{scenario_id}.json")
            if not scenario_file.exists():
                self.send_error(404)
                return
            data = json.loads(scenario_file.read_text())
            imported = data.get("config", {})
            applied = 0
            for section_name, values in imported.items():
                section = section_name.rsplit(".", 1)[-1] if "." in section_name else section_name
                if write_config_section(Path("/etc/rnas"), section, values):
                    applied += 1
            self.json(dict(success=True, scenario=data.get("name", scenario_id), applied=applied, total=len(imported)))
        elif path == "/api/dictionary":
            entries = load_all(str(DICT_DIR))
            self.json(dict(success=True, vendors=list(set(e["vendor"] for e in entries.values())), count=len(entries), attributes=entries))
        elif path.startswith("/api/dictionary/search"):
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0]
            results = dict_search(q, str(DICT_DIR))
            self.json(dict(success=True, query=q, count=len(results), results=results))
        elif path == "/api/config/apply":
            for svc, sub in [("accel-ppp", "accel-ppp"), ("dnsmasq", "dnsmasq"), ("firewall", "firewall"), ("snmp", "snmp")]:
                subprocess.run(["python3", "/usr/bin/rnas-config", "--root", "/etc/rnas",
                                "generate", sub, "-o", f"/var/run/rnas/{sub}.conf"],
                               capture_output=True, timeout=5)
            subprocess.run(["systemctl", "reload-or-restart", "rnas-accel-ppp", "rnas-dnsmasq"], capture_output=True, timeout=10)
            self.json(dict(success=True, message="Configuration applied"))
        elif path == "/api/config/export":
            config = walk_config_tree(Path("/etc/rnas"))
            data = {"rnas_version": "3.0", "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "config": {k: dict(v) for k, v in config.items()}}
            self.json(data)
        elif path == "/api/config/import":
            content_len = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_len))
            imported = data.get("config", {})
            applied = 0
            for section_name, values in imported.items():
                section = section_name.rsplit(".", 1)[-1] if "." in section_name else section_name
                if write_config_section(Path("/etc/rnas"), section, values):
                    applied += 1
            self.json(dict(success=True, imported=applied, total=len(imported)))
        elif path == "/api/config/snapshots":
            snap_dir = Path("/var/lib/rnas/snapshots")
            snap_dir.mkdir(parents=True, exist_ok=True)
            snaps = []
            for f in sorted(snap_dir.glob("*.json"), reverse=True):
                snaps.append({"id": f.stem, "date": time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)), "size": f.stat().st_size})
            self.json(dict(snapshots=snaps[:10]))
        elif path == "/api/config/snapshot":
            snap_dir = Path("/var/lib/rnas/snapshots")
            snap_dir.mkdir(parents=True, exist_ok=True)
            config = walk_config_tree(Path("/etc/rnas"))
            snap_name = f"snap-{time.strftime('%Y%m%d-%H%M%S')}"
            data = {"rnas_version": "3.0", "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "config": {k: dict(v) for k, v in config.items()}}
            (snap_dir / f"{snap_name}.json").write_text(json.dumps(data, indent=2))
            self.json(dict(success=True, id=snap_name))
        elif path.startswith("/api/config/snapshot/") and path.endswith("/restore"):
            snap_id = path.split("/")[4]
            snap_file = Path(f"/var/lib/rnas/snapshots/{snap_id}.json")
            if not snap_file.exists():
                self.send_error(404, "Snapshot not found")
                return
            data = json.loads(snap_file.read_text())
            imported = data.get("config", {})
            restored = 0
            for section_name, values in imported.items():
                if write_config_section(Path("/etc/rnas"), section_name.replace(".", "/", 1) if "." in section_name else section_name, values):
                    restored += 1
            self.json(dict(success=True, restored=restored, message=f"Restored {restored} sections from {snap_id}"))
        elif path.startswith("/api/config/snapshot/") and self.command == "DELETE":
            snap_id = path.split("/")[4]
            snap_file = Path(f"/var/lib/rnas/snapshots/{snap_id}.json")
            if snap_file.exists():
                snap_file.unlink()
            self.json(dict(success=True))
        elif path == "/api/routing/status":
            ospf, bgp = {}, {}
            try:
                out = subprocess.run(["vtysh", "-c", "show ip ospf neighbor"], capture_output=True, text=True, timeout=5).stdout
                neighbors = []
                for line in out.splitlines():
                    if line.strip() and not line.startswith("Neighbor") and not line.startswith("-"):
                        cols = line.split()
                        if len(cols) >= 5: neighbors.append({"id": cols[0], "state": cols[2], "address": cols[4], "iface": cols[5] if len(cols)>5 else ""})
                ospf["neighbors"] = neighbors
            except: ospf["neighbors"] = []
            try:
                out = subprocess.run(["vtysh", "-c", "show bgp summary"], capture_output=True, text=True, timeout=5).stdout
                peers, routes = [], []
                for line in out.splitlines():
                    cols = line.split()
                    if len(cols) >= 10 and cols[0].count(".") == 3:
                        peers.append({"peer": cols[0], "as": cols[2], "rcv": cols[3], "sent": cols[4], "uptime": cols[8], "state": cols[9] if len(cols)>9 else ""})
                rout = subprocess.run(["vtysh", "-c", "show ip route"], capture_output=True, text=True, timeout=5).stdout
                for line in rout.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0][0] in "OBCK" and ">" in line:
                        routes.append({"network": parts[1] if len(parts)>1 else "", "nexthop": parts[2] if len(parts)>2 else "", "proto": parts[0]})
                bgp = {"peers": peers, "routes": routes[:20]}
            except: bgp = {"peers": [], "routes": []}
            self.json({"ospf": ospf, "bgp": bgp})
        elif path == "/api/tunnels":
            try:
                out = subprocess.run(["ip", "-br", "-d", "link"], capture_output=True, text=True, timeout=5).stdout
                tunnels = []
                for line in out.splitlines():
                    for t in ["gre", "ipip", "vxlan", "eoip"]:
                        if t in line.lower() and "gretap" not in line.lower():
                            parts = line.split()
                            tunnels.append({"name": parts[0], "up": "UP" in line, "type": t, "local": "", "remote": "", "inner_ip": ""})
                self.json({"tunnels": tunnels})
            except: self.json({"tunnels": []})
        elif path == "/api/vlans":
            mod_loaded = subprocess.run("lsmod | grep -q 8021q", shell=True).returncode == 0
            vlan_mon = subprocess.run("lsmod | grep -q vlan_mon", shell=True).returncode == 0 or True
            try:
                out = subprocess.run(["ip", "-br", "link"], capture_output=True, text=True, timeout=5).stdout
                ifaces = []
                for line in out.splitlines():
                    if "." in line.split()[0]:
                        parts = line.split()
                        name = parts[0]; parent = name.split(".")[0]
                        ifaces.append({"name": name, "id": name.split(".")[-1], "up": "UP" in line, "parent": parent})
                self.json({"module": "loaded" if mod_loaded else "missing", "kernel": "loaded" if mod_loaded else "missing", "interfaces": ifaces[:20]})
            except: self.json({"module": "unknown", "kernel": "unknown", "interfaces": []})
        elif path == "/api/netflow":
            running = subprocess.run(["systemctl", "is-active", "softflowd"], capture_output=True, text=True).stdout.strip() == "active"
            self.json({"running": running, "collector": "192.168.0.202:2055", "interface": "ens33", "format": "netflow_v5"})
        elif path == "/api/dhcp-relay":
            running = subprocess.run(["systemctl", "is-active", "rnas-dhcp-relay"], capture_output=True, text=True).stdout.strip() == "active"
            self.json({"running": running, "upstream": "192.168.0.202:67", "giaddr": "192.168.100.1"})
        elif path == "/api/hotspot/status":
            portal_active = os.path.exists("/opt/rnas-web/static/hotspot/login.html")
            ipt = "Active" if subprocess.run("iptables -t nat -L rnas-hotspot -n 2>/dev/null | grep -q DNAT", shell=True).returncode == 0 else "Inactive"
            self.json({"portal": "Active" if portal_active else "Inactive",
                       "auth": "Active",
                       "iptables": ipt})
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
