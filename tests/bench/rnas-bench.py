#!/usr/bin/env python3
"""RNAS Performance Benchmark — measures auth latency, throughput, and session rate"""
import subprocess, time, json, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

RADIUS_SERVER = "192.168.0.202:1812"
SECRET = "testing123"
USER = "testuser"
PASS = "testpass"
SSH = ["sshpass", "-p", "123456", "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5"]

def rad_auth():
    """Single RADIUS auth request — returns latency in ms"""
    start = time.time()
    result = subprocess.run(
        ["radclient", "-r", "1", "-t", "5", RADIUS_SERVER, "auth", SECRET],
        input=f"User-Name={USER},User-Password={PASS}",
        capture_output=True, text=True, timeout=10
    )
    elapsed = (time.time() - start) * 1000
    ok = "Access-Accept" in result.stdout
    return elapsed, ok

def concurrent_auth(n):
    """N concurrent RADIUS auth requests — returns list of latencies"""
    results = []
    with ThreadPoolExecutor(max_workers=n) as ex:
        futures = [ex.submit(rad_auth) for _ in range(n)]
        for f in as_completed(futures):
            results.append(f.result())
    return results

def measure_pppoe_rate(count=10):
    """Measure PPPoE session establishment rate"""
    start = time.time()
    subprocess.run(
        SSH + ["root@192.168.0.201", f"for i in $(seq 1 {count}); do timeout 15 pppd call rnas-pppoe nodetach >/dev/null 2>&1 & done; wait"],
        timeout=count * 15 + 10
    )
    elapsed = time.time() - start
    sessions = subprocess.run(
        SSH + ["root@192.168.0.203", "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd show sessions 2>&1 | grep -c active || echo 0"],
        capture_output=True, text=True, timeout=15
    ).stdout.strip()
    subprocess.run(
        SSH + ["root@192.168.0.203", "/home/lancer/projects/RNAS/build/accel-ppp/install/usr/bin/accel-cmd terminate all 2>/dev/null"],
        capture_output=True, timeout=10
    )
    return elapsed, int(sessions) if sessions.isdigit() else 0

def main():
    print("=== RNAS Performance Benchmark ===")
    print(f"Target: {RADIUS_SERVER}")
    report = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "target": RADIUS_SERVER}

    # 1. Single auth latency (10 samples)
    print("\n1. Single Auth Latency (10 samples)...")
    latencies = []
    for i in range(10):
        lat, ok = rad_auth()
        if ok:
            latencies.append(lat)
        sys.stdout.write("." if ok else "X")
        sys.stdout.flush()
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    report["single_auth"] = {"samples": len(latencies), "avg_ms": round(avg_lat, 1), "min_ms": round(min(latencies), 1) if latencies else 0, "max_ms": round(max(latencies), 1) if latencies else 0}
    print(f"\n   Average: {avg_lat:.1f}ms (min:{min(latencies):.1f}, max:{max(latencies):.1f})")

    # 2. Concurrent auth throughput (10, 20, 50)
    print("\n2. Concurrent Auth Throughput...")
    throughputs = {}
    for n in [10, 20, 50]:
        start = time.time()
        results = concurrent_auth(n)
        elapsed = time.time() - start
        ok_count = sum(1 for _, ok in results if ok)
        rps = ok_count / elapsed if elapsed > 0 else 0
        latencies = [l for l, ok in results if ok]
        avg_concurrent = sum(latencies) / len(latencies) if latencies else 0
        throughputs[str(n)] = {"requests": n, "success": ok_count, "duration_s": round(elapsed, 2), "rps": round(rps, 1), "avg_ms": round(avg_concurrent, 1)}
        print(f"   {n} concurrent: {ok_count}/{n} success, {rps:.1f} req/s, avg {avg_concurrent:.1f}ms")
    report["throughput"] = throughputs

    # 3. PPPoE session rate
    print("\n3. PPPoE Session Establishment Rate (10 sessions)...")
    elapsed, count = measure_pppoe_rate(10)
    rate = count / elapsed if elapsed > 0 else 0
    report["pppoe_rate"] = {"sessions": count, "duration_s": round(elapsed, 2), "rate_per_sec": round(rate, 2)}
    print(f"   {count} sessions in {elapsed:.1f}s = {rate:.2f} sessions/sec")

    # 4. Generate report
    report_path = f"/var/lib/rnas/benchmarks/bench-{time.strftime('%Y%m%d-%H%M%S')}.json"
    subprocess.run(["mkdir", "-p", "/var/lib/rnas/benchmarks"])
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {report_path}")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
