#!/usr/bin/env python3
"""RNAS Protocol Capture & Replay — record and replay RADIUS exchanges"""
import subprocess, time, json, os, sys, argparse
from pathlib import Path

CAPTURE_DIR = Path("/var/lib/rnas/captures")

def capture(duration=30, output=None):
    """Capture RADIUS traffic using tcpdump"""
    if output is None:
        output = CAPTURE_DIR / f"radius-{time.strftime('%Y%m%d-%H%M%S')}.pcap"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Capturing RADIUS traffic for {duration}s to {output}...")
    subprocess.run([
        "tcpdump", "-i", "any", "-w", str(output),
        "-G", str(duration), "-W", "1",
        "udp port 1812 or udp port 1813 or udp port 3799"
    ], timeout=duration + 5)
    size = output.stat().st_size if output.exists() else 0
    print(f"Captured {size} bytes to {output}")
    return str(output)


def replay(pcap_file, target="192.168.0.202:1812", secret="testing123", speed=1.0):
    """Replay captured RADIUS packets using tcpreplay or radclient"""
    pcap = Path(pcap_file)
    if not pcap.exists():
        print(f"Error: {pcap} not found")
        return

    # Parse pcap with tshark and extract RADIUS attributes
    print(f"Parsing {pcap}...")
    result = subprocess.run([
        "tshark", "-r", str(pcap), "-T", "fields",
        "-e", "radius.User-Name", "-e", "radius.User-Password",
        "-e", "radius.Calling-Station-Id", "-e", "radius.Framed-IP-Address",
        "-e", "radius.Acct-Session-Id", "-e", "radius.Acct-Status-Type",
        "-E", "separator=|"
    ], capture_output=True, text=True, timeout=10)

    if result.returncode != 0 or not result.stdout.strip():
        # Fallback: use radclient to replay directly
        print("tshark not available, using raw replay mode")
        return raw_replay(pcap_file, target, secret)

    sessions = []
    for line in result.stdout.strip().splitlines():
        fields = line.split("|")
        if fields:
            sessions.append({k: v for k, v in zip(["user", "pass", "calling", "ip", "sid", "acct_type"], fields) if v})

    print(f"Found {len(sessions)} RADIUS exchanges")
    for i, s in enumerate(sessions):
        user = s.get("user", "unknown")
        print(f"  [{i+1}] User={user}")
        if s.get("acct_type") == "1":  # Start
            print(f"       Accounting-Start, Session={s.get('sid', 'N/A')}")

    print(f"\nReplay {len(sessions)} sessions at {speed}x speed...")
    for i, s in enumerate(sessions):
        user = s.get("user", "testuser")
        pwd = s.get("pass", "testpass")
        if pwd:
            subprocess.run([
                "radclient", "-r", "1", "-t", "3", target, "auth", secret
            ], input=f"User-Name={user},User-Password={pwd}", capture_output=True, text=True, timeout=5)
        print(f"  [{i+1}/{len(sessions)}] Replayed {user}")
        if speed > 0:
            time.sleep(1.0 / speed)


def raw_replay(pcap_file, target, secret):
    """Replay raw packets using tcpreplay"""
    result = subprocess.run([
        "tcpreplay", "--intf1=ens33", "--topspeed", str(pcap_file)
    ], capture_output=True, text=True, timeout=30)
    print(result.stdout[-200:] if result.stdout else "Replay complete")


def list_captures():
    """List available capture files"""
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(CAPTURE_DIR.glob("*.pcap"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[:10]:
        size = f.stat().st_size
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
        print(f"  {f.name:40s} {size:>8d} bytes  {mtime}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RNAS Protocol Capture & Replay")
    p.add_argument("action", choices=["capture", "replay", "list"], help="Action")
    p.add_argument("--duration", type=int, default=30, help="Capture duration (seconds)")
    p.add_argument("--file", help="PCAP file to replay or save to")
    p.add_argument("--target", default="192.168.0.202:1812", help="RADIUS target")
    p.add_argument("--secret", default="testing123", help="RADIUS secret")
    p.add_argument("--speed", type=float, default=1.0, help="Replay speed multiplier")
    args = p.parse_args()

    if args.action == "capture":
        capture(args.duration, args.file)
    elif args.action == "replay":
        replay(args.file, args.target, args.secret, args.speed)
    elif args.action == "list":
        list_captures()
