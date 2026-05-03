#!/usr/bin/env python3
"""RNAS Bandwidth Test — measures throughput through PPP sessions"""
import socket, time, sys, argparse, threading

def server(port=5201):
    """TCP sink - receives data and reports throughput"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f'BW Server listening on :{port}')
    conn, addr = s.accept()
    print(f'Connected: {addr[0]}')
    total = 0
    start = time.time()
    while True:
        data = conn.recv(65536)
        if not data:
            break
        total += len(data)
    elapsed = time.time() - start
    mbps = (total * 8 / 1_000_000) / elapsed if elapsed > 0 else 0
    print(f'Received: {total/1024/1024:.1f} MB in {elapsed:.1f}s = {mbps:.1f} Mbps')
    conn.close()
    s.close()

def client(target, port=5201, duration=5):
    """TCP source - sends data and reports throughput"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((target, port))
    except Exception as e:
        print(f'Connect failed: {e}')
        return
    print(f'Connected to {target}:{port}')
    total = 0
    start = time.time()
    chunk = b'X' * 65536
    while time.time() - start < duration:
        try:
            sent = s.send(chunk)
            total += sent
        except:
            break
    elapsed = time.time() - start
    mbps = (total * 8 / 1_000_000) / elapsed if elapsed > 0 else 0
    print(f'Sent: {total/1024/1024:.1f} MB in {elapsed:.1f}s = {mbps:.1f} Mbps')
    s.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='RNAS Bandwidth Test')
    p.add_argument('mode', choices=['server', 'client'], help='Server or client mode')
    p.add_argument('--target', default='127.0.0.1', help='Target IP (client mode)')
    p.add_argument('--port', type=int, default=5201, help='Port')
    p.add_argument('--duration', type=int, default=5, help='Test duration (seconds)')
    args = p.parse_args()
    if args.mode == 'server':
        server(args.port)
    else:
        client(args.target, args.port, args.duration)
