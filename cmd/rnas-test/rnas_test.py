#!/usr/bin/env python3
"""
RNAS Test CLI — stress testing and scenario execution.

Usage:
    rnas-test stress --cpe-count 100 --proto pppoe
    rnas-test stress --cpe-count 5 --dry-run          # topology only, safe
    rnas-test stress --cpe-count 20 --attach-iface eth1
    rnas-test run scenarios/pppoe-batch.yaml
"""

import argparse
import json
import sys
from pathlib import Path

from stress_engine import StressEngine, StressConfig


def cmd_stress(args):
    config = StressConfig(
        cpe_count=args.cpe_count,
        protocol=args.proto,
        username_prefix=args.user_prefix,
        password=args.password,
        rate=args.rate,
        duration=args.duration,
        attach_iface=args.attach_iface or "",
        dry_run=args.dry_run,
        peer_file=args.peer_file,
    )
    engine = StressEngine(config)
    try:
        results = engine.run()
        print(json.dumps(results, indent=2))
    finally:
        engine.teardown()


def cmd_run(args):
    from scenario_engine import run_scenario_file
    try:
        result = run_scenario_file(Path(args.file), format=args.format)
    except ValueError as e:
        print(f"Scenario invalid: {e}", file=sys.stderr)
        sys.exit(1)
    if args.format == "junit":
        print(result.pop("junit_xml"))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="RNAS Test Engine")
    sub = parser.add_subparsers(dest="command")

    # Stress test
    stress = sub.add_parser("stress", help="Bulk CPE stress test via netns")
    stress.add_argument("--cpe-count", type=int, default=20)
    stress.add_argument("--proto", default="pppoe", choices=["pppoe", "pptp"])
    stress.add_argument("--user-prefix", default="testuser")
    stress.add_argument("--password", default="testpass")
    stress.add_argument("--rate", type=float, default=5.0, help="Sessions per second")
    stress.add_argument("--duration", type=int, help="Max test duration in seconds")
    stress.add_argument("--attach-iface", help="accel-ppp NIC to bridge (dedicated test NIC!)")
    stress.add_argument("--dry-run", action="store_true", help="Create topology only, no dialing")
    stress.add_argument("--peer-file", default="rnas-pppoe", help="pppd peer name in netns")

    # Scenario runner
    run = sub.add_parser("run", help="Execute a YAML scenario")
    run.add_argument("file", help="Path to scenario YAML")
    run.add_argument("--format", default="json", choices=["json", "junit"],
                     help="Report format (default: json)")

    args = parser.parse_args()
    if args.command == "stress":
        cmd_stress(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
