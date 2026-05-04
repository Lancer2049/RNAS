#!/usr/bin/env python3
"""RNAS RADIUS Compatibility Test — automated VSA testing"""
import subprocess, json, sys, time
from urllib.request import urlopen, Request

RADIUS_API = "http://192.168.0.203:8099/api"
DICT_API = f"{RADIUS_API}/dictionary/search?q="
TEST_API = f"{RADIUS_API}/tools/radius-send"
USER = "testuser"
PASS = "testpass"

def api_post(url, data):
    req = Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urlopen(req, timeout=10).read())

def api_get(url):
    return json.loads(urlopen(url, timeout=10).read())

def test_attr(attr_name, value="test"):
    """Send Access-Request with a specific VSA attribute"""
    result = api_post(TEST_API, {
        "server": "192.168.0.202:1812",
        "secret": "testing123",
        "type": "auth",
        "attributes": [
            {"name": "User-Name", "value": USER},
            {"name": "User-Password", "value": PASS},
            {"name": attr_name, "value": value}
        ]
    })
    return "Access-Accept" in result.get("output", "")

def test_vendor(vendor):
    """Test all attributes for a specific vendor"""
    results = api_get(f"{DICT_API}{vendor.lower()}")
    attrs = results.get("results", [])
    if not attrs:
        print(f"  No attributes found for {vendor}")
        return []

    passed = []
    failed = []
    skipped = 0

    for a in attrs:
        name = a["name"]
        atype = a["type"]
        if atype in ("octets", "ipv6addr", "ipv6prefix", "ifid"):
            skipped += 1
            continue
        value = "test"
        if atype == "integer":
            value = "100"
        elif atype == "ipaddr":
            value = "192.168.100.1"
        elif atype == "date":
            value = "20260503120000"

        try:
            ok = test_attr(name, value)
            if ok:
                passed.append(name)
                sys.stdout.write(".")
            else:
                failed.append(name)
                sys.stdout.write("✗")
        except Exception as e:
            failed.append(f"{name}({e})")
            sys.stdout.write("E")
        sys.stdout.flush()
        time.sleep(0.05)

    print()
    return passed, failed, skipped

def main():
    vendors = ["Huawei", "Cisco", "H3C", "Mikrotik", "Microsoft", "WISPr"]
    total_pass = 0
    total_fail = 0
    total_skip = 0

    print("=== RNAS RADIUS Compatibility Test ===")
    print(f"User: {USER} | Target: 192.168.0.202:1812")
    print()

    for vendor in vendors:
        print(f"--- {vendor} ---")
        p, f, s = test_vendor(vendor)
        total_pass += len(p)
        total_fail += len(f)
        total_skip += s
        if f:
            print(f"  Failed: {', '.join(f[:5])}{'...' if len(f) > 5 else ''}")
        print(f"  {len(p)} passed, {len(f)} failed, {s} skipped")
        print()

    total = total_pass + total_fail
    rate = total_pass * 100 / total if total > 0 else 0
    print(f"=== Results: {total_pass}/{total} ({rate:.0f}%) passed, {total_skip} skipped ===")
    return 0 if total_fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
