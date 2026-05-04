#!/usr/bin/env python3
"""RNAS VSA Compatibility Matrix — quick smoke test of vendor attributes"""
import subprocess, json, time

RADIUS = "192.168.0.202:1812"
SECRET = "testing123"

def test_vsa(name, value="test"):
    result = subprocess.run(
        ["radclient", "-r", "1", "-t", "3", RADIUS, "auth", SECRET],
        input=f"User-Name=testuser,User-Password=testpass,{name}={value}",
        capture_output=True, text=True, timeout=5
    )
    return "Access-Accept" in result.stdout

smoke_tests = {
    "Huawei":   "Huawei-QOS-Profile-Name=gold",
    "H3C":      "H3C-Exec-Privilege=3",
    "Cisco":    "Cisco-AVPair=test-value",
    "ZTE":      "ZTE-CAR-Profile-Name=premium",
    "Juniper":  "Juniper-Role-Name=super-user",
    "Aruba":    "Aruba-User-Role=guest",
    "Ericsson": "Ericsson-QoS-Profile=gold",
    "Arista":   "Arista-User-Role=operator",
    "NVIDIA":   "NVIDIA-User-Role=netadmin",
    "Ruijie":   "Ruijie-User-Role=admin",
    "MikroTik": "Mikrotik-Rate-Limit=10M",
    "Microsoft":"MS-Primary-DNS-Server=8.8.8.8",
    "WISPr":    "WISPr-Location-ID=test",
}

print("=== RNAS VSA Compatibility Matrix ===")
print(f"Target: {RADIUS}")
print()

passed = 0
failed = 0
for vendor, test in smoke_tests.items():
    name, value = test.split("=", 1)
    ok = test_vsa(name, value)
    status = "✅" if ok else "❌"
    print(f"  {status} {vendor:12s} {name}")
    if ok: passed += 1
    else: failed += 1
    time.sleep(0.1)

print(f"\n=== {passed}/{passed+failed} vendors compatible ===")
