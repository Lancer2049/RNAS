#!/usr/bin/env python3
"""RNAS QoS Daemon v2 — per-user bandwidth control via tc + iptables"""
import subprocess, time, re

LOG_FILE = "/var/log/rnas-qos.log"
MANAGED = {}
INTERVAL = 5

TIERS = {
    "bwtest":   {"mark": 30, "rate": "5mbit",  "ceil": "10mbit"},
    "testuser": {"mark": 20, "rate": "10mbit", "ceil": "20mbit"},
    "DEFAULT":  {"mark": 40, "rate": "2mbit",  "ceil": "5mbit"},
}

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts} {msg}\n")

def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except:
        return ""

def get_sessions():
    out = run("/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd show sessions ifname,username,ip,type,state,uptime-raw")
    sessions = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6 and re.match(r"\d+\.\d+\.\d+\.\d+", parts[2].strip()):
            sessions.append({
                "ifname": parts[0].strip(),
                "username": parts[1].strip(),
                "ip": parts[2].strip()
            })
    return sessions

def apply_qos(ip, ifname, username):
    if ip in MANAGED:
        return
    tier = TIERS.get(username, TIERS["DEFAULT"])
    m, rate, ceil = tier["mark"], tier["rate"], tier["ceil"]
    run(f"iptables -t mangle -A INPUT -s {ip} -j MARK --set-mark {m}")
    run(f"iptables -t mangle -A OUTPUT -d {ip} -j MARK --set-mark {m}")
    run(f"iptables -t mangle -A FORWARD -s {ip} -j MARK --set-mark {m}")
    run(f"tc qdisc add dev {ifname} root handle 2: htb default 10 2>/dev/null")
    run(f"tc class add dev {ifname} parent 2: classid 2:1 htb rate 100mbit ceil 100mbit 2>/dev/null")
    run(f"tc class add dev {ifname} parent 2:1 classid 2:{m} htb rate {rate} ceil {ceil} 2>/dev/null")
    run(f"tc qdisc add dev {ifname} parent 2:{m} handle 22{m}: sfq perturb 10 2>/dev/null")
    run(f"tc filter add dev {ifname} parent 2: prio 1 protocol ip handle {m} fw flowid 2:{m} 2>/dev/null")
    MANAGED[ip] = {"mark": m, "ifname": ifname}
    log(f"ADD {username} {ip} mark={m} rate={rate}")

def remove_qos(ip):
    if ip not in MANAGED:
        return
    m = MANAGED[ip]["mark"]
    run(f"iptables -t mangle -D INPUT -s {ip} -j MARK --set-mark {m}")
    run(f"iptables -t mangle -D OUTPUT -d {ip} -j MARK --set-mark {m}")
    run(f"iptables -t mangle -D FORWARD -s {ip} -j MARK --set-mark {m}")
    log(f"DEL {ip}")
    del MANAGED[ip]

def main():
    log("STARTED v2")
    while True:
        try:
            sessions = get_sessions()
            active_ips = {s["ip"]: s for s in sessions}
            for s in sessions:
                apply_qos(s["ip"], s["ifname"], s["username"])
            for ip in list(MANAGED.keys()):
                if ip not in active_ips:
                    remove_qos(ip)
        except Exception as e:
            log(f"ERROR {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
