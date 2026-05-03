import socket, struct, time
UPSTREAM = ("192.168.0.202", 67)
GIADDR = "192.168.100.1"
LOG = "/var/log/rnas-dhcp-relay.log"
def log(m):
    with open(LOG, "a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", 67))
sock.settimeout(30)
pending = {}
log(f"STARTED v2 giaddr={GIADDR}")

while True:
    try:
        data, client = sock.recvfrom(4096)
    except socket.timeout:
        continue

    xid = data[4:8].hex()
    giaddr_bytes = socket.inet_aton(GIADDR)
    data_out = data[:24] + giaddr_bytes + data[28:]
    log(f"RELAY {len(data)}B from {client[0]} xid={xid}")
    sock.sendto(data_out, UPSTREAM)
    pending[xid] = client

    # Wait for OFFER on the SAME socket (dhcpd sends to giaddr:67)
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
