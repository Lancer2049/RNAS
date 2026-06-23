import socket, struct, time, os
UPSTREAM = ("192.168.0.202", 67)
GIADDR = "192.168.100.1"
OPTION82_CIRCUIT_ID = os.environ.get("RNAS_RELAY_CIRCUIT_ID", "rnas-port1")
OPTION82_REMOTE_ID = os.environ.get("RNAS_RELAY_REMOTE_ID", "rnas")
LOG = "/var/log/rnas-dhcp-relay.log"

def log(m):
    with open(LOG, "a") as f: f.write(f"{time.strftime('%H:%M:%S')} {m}\n")

def add_option82(data, client_addr):
    """Insert DHCP Option 82 (Relay Agent Information) into packet"""
    # DHCP option 82 format: code(1) len(1) sub-options...
    # Sub-option 1 = Circuit ID, Sub-option 2 = Remote ID
    circuit = OPTION82_CIRCUIT_ID.encode()
    remote = OPTION82_REMOTE_ID.encode()
    # Build sub-options
    sub_opts = struct.pack("!BB", 1, len(circuit)) + circuit
    sub_opts += struct.pack("!BB", 2, len(remote)) + remote
    # Build option 82
    opt82 = struct.pack("!BB", 82, len(sub_opts)) + sub_opts
    # Insert before DHCP END option (0xFF) or append after existing options
    if data[-1:] == b'\xff':
        return data[:-1] + opt82 + b'\xff'
    return data + opt82

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", 67))
sock.settimeout(30)
pending = {}
log(f"STARTED v3 giaddr={GIADDR} opt82_circuit={OPTION82_CIRCUIT_ID}")

while True:
    try:
        data, client = sock.recvfrom(4096)
    except socket.timeout:
        continue

    xid = data[4:8].hex()
    giaddr_bytes = socket.inet_aton(GIADDR)
    # Insert Option 82 if message type is DISCOVER (1) or REQUEST (3)
    msg_type = data[0]
    data_out = data[:24] + giaddr_bytes + data[28:]
    # Remove existing Option 82 if present, then add fresh
    data_out = add_option82(data_out, client[0])
    
    log(f"RELAY {len(data)}B {msg_type} from {client[0]} xid={xid} circuit={OPTION82_CIRCUIT_ID}")
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
