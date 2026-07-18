#!/usr/bin/env python3
"""
RNAS Test CLI — stress testing and scenario execution.

Usage:
    rnas-test stress --cpe-count 100 --proto pppoe
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
        protocol=args.protocol,
        username_prefix=args.user_prefix,
        password=args.password,
        rate=args.rate,
        duration=args.duration,
    )
    engine = StressEngine(config)
    try:
        results = engine.run()
        print(json.dumps(results, indent=2))
    finally:
        engine.teardown()


def main():
    parser = argparse.ArgumentParser(description="RNAS Test Engine")
    sub = parser.add_subparsers(dest="command")

    # Stress test
    stress = sub.add_parser("stress", help="Bulk CPE stress test via netns")
    stress.add_argument("--cpe-count", type=int, default=100)
    stress.add_argument("--proto", default="pppoe", choices=["pppoe", "pptp"])
    stress.add_argument("--user-prefix", default="testuser")
    stress.add_argument("--password", default="testpass")
    stress.add_argument("--rate", type=float, default=10.0, help="Sessions per second")
    stress.add_argument("--duration", type=int, help="Max test duration in seconds")

    # Scenario runner
    sub.add_parser("run", help="Run a YAML scenario (Phase 3-B)")

    args = parser.parse_args()
    if args.command == "stress":
        cmd_stress(args)
    elif args.command == "run":
        print("Scenario runner: Phase 3-B WIP", file=sys.stderr)
        sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
