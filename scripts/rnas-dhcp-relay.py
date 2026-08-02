#!/usr/bin/env python3
"""DHCP Relay Agent — forwards DHCP to upstream server with giaddr + Option 82.

Reads relay settings from /etc/rnas/network.d/dhcp.conf [relay] section:
enabled / upstream / giaddr / interface / option82 / circuit_id / remote_id
"""
import socket
import struct
import time
import os
import configparser
from pathlib import Path

CONF_PATH = Path(os.environ.get("RNAS_RELAY_CONF", "/etc/rnas/network.d/dhcp.conf"))
LOG = os.environ.get("RNAS_RELAY_LOG", "/var/log/rnas-dhcp-relay.log")


def load_config():
    """Load relay settings from the RNAS config tree, with sane defaults."""
    upstream = "192.168.0.202"
    giaddr = "192.168.100.1"
    iface = "ens33"
    option82 = False
    circuit_id = "rnas-port1"
    remote_id = "rnas"
    try:
        cp = configparser.ConfigParser()
        cp.read(str(CONF_PATH))
        if cp.has_section("relay"):
            s = cp["relay"]
            upstream = s.get("upstream", upstream)
            giaddr = s.get("giaddr", giaddr)
            iface = s.get("interface", iface)
            option82 = s.get("option82", "no").strip().lower() == "yes"
            circuit_id = s.get("circuit_id", circuit_id)
            remote_id = s.get("remote_id", remote_id)
    except Exception:
        pass
    return upstream, giaddr, iface, option82, circuit_id, remote_id


def log(m):
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {m}\n")


def add_option82(data, circuit, remote):
    """Insert DHCP Option 82 (Relay Agent Information) into packet.

    Sub-option 1 = Circuit ID, Sub-option 2 = Remote ID. Inserted before the
    DHCP END option (0xFF) so upstream RADIUS can identify the access port.
    """
    circuit_b = circuit.encode()
    remote_b = remote.encode()
    sub_opts = struct.pack("!BB", 1, len(circuit_b)) + circuit_b
    sub_opts += struct.pack("!BB", 2, len(remote_b)) + remote_b
    opt82 = struct.pack("!BB", 82, len(sub_opts)) + sub_opts
    if data[-1:] == b"\xff":
        return data[:-1] + opt82 + b"\xff"
    return data + opt82


upstream, giaddr, iface, option82, circuit_id, remote_id = load_config()
UPSTREAM = (upstream, 67)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", 67))
sock.settimeout(30)
pending = {}
log(f"STARTED upstream={upstream}:67 giaddr={giaddr} iface={iface} "
    f"option82={'on' if option82 else 'off'} circuit={circuit_id}")

while True:
    try:
        data, client = sock.recvfrom(4096)
    except socket.timeout:
        continue

    xid = data[4:8].hex()
    giaddr_bytes = socket.inet_aton(giaddr)
    data_out = data[:24] + giaddr_bytes + data[28:]
    if option82:
        data_out = add_option82(data_out, circuit_id, remote_id)

    log(f"RELAY {len(data)}B from {client[0]} xid={xid} "
        f"circuit={circuit_id if option82 else '-'}")
    sock.sendto(data_out, UPSTREAM)
    pending[xid] = client

    old_timeout = sock.gettimeout()
    sock.settimeout(5)
    try:
        reply, _ = sock.recvfrom(4096)
        rxid = reply[4:8].hex()
        if rxid in pending:
            orig = pending.pop(rxid)
            sock.sendto(reply, orig)
            log(f"REPLY {len(reply)}B -> {orig[0]}")
    except socket.timeout:
        log(f"TIMEOUT {xid}")
        pending.pop(xid, None)
    sock.settimeout(old_timeout)
