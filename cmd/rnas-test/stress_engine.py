#!/usr/bin/env python3
"""
RNAS Stress Test Engine — network namespace-based bulk CPE simulation.

Creates N virtual CPEs via Linux network namespaces, each running pppd to
simulate concurrent PPPoE sessions against the local accel-ppp server.
Validates RADIUS auth/acct and collects performance metrics.

Architecture:
    ┌─────────────────────────────────┐
    │         RNAS host               │
    │  ┌──────┐ ┌──────┐      ┌──────┐│
    │  │netns │ │netns │ ...  │netns ││
    │  │cpe-01│ │cpe-02│      │cpe-NN││
    │  │pppd  │ │pppd  │      │pppd  ││
    │  └──┬───┘ └──┬───┘      └──┬───┘│
    │     └────┬───┘             │    │
    │       veth bridge          │    │
    │          │                 │    │
    │     accel-ppp (SUT)        │    │
    └──────────────────────────────┘

Usage:
    rnas-test stress --cpe-count 100 --proto pppoe --user-prefix testuser --password testpass
    rnas-test stress --cpe-count 50 --rate 5/s --duration 60s
"""

import subprocess
import time
import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StressConfig:
    cpe_count: int = 100
    protocol: str = "pppoe"
    username_prefix: str = "testuser"
    password: str = "testpass"
    rate: float = 10.0  # sessions per second
    duration: Optional[int] = None  # seconds, None = until all connected
    bridge_name: str = "rnas-br0"
    subnet: str = "10.99.0"


class StressEngine:
    """Manages bulk PPPoE session creation/destruction via Linux netns."""

    def __init__(self, config: StressConfig):
        self.config = config
        self.namespaces: list[str] = []
        self.results: dict = {"connected": 0, "failed": 0, "times": [], "errors": []}

    def setup_network(self):
        """Create bridge and veth pairs for all CPEs."""
        subprocess.run(["ip", "link", "add", self.config.bridge_name, "type", "bridge"], capture_output=True)
        subprocess.run(["ip", "link", "set", self.config.bridge_name, "up"], capture_output=True)

        for i in range(self.config.cpe_count):
            ns = f"cpe-{i:03d}"
            self.namespaces.append(ns)
            subprocess.run(["ip", "netns", "add", ns], capture_output=True)
            subprocess.run(["ip", "link", "add", f"veth-{ns}", "type", "veth", "peer", f"vpeer-{ns}"], capture_output=True)
            subprocess.run(["ip", "link", "set", f"vpeer-{ns}", "netns", ns], capture_output=True)
            subprocess.run(["ip", "link", "set", f"veth-{ns}", "master", self.config.bridge_name], capture_output=True)
            subprocess.run(["ip", "link", "set", f"veth-{ns}", "up"], capture_output=True)
            subprocess.run(["ip", "netns", "exec", ns, "ip", "link", "set", "lo", "up"], capture_output=True)
            subprocess.run(["ip", "netns", "exec", ns, "ip", "link", "set", f"vpeer-{ns}", "up"], capture_output=True)
            subprocess.run(["ip", "netns", "exec", ns, "ip", "addr", "add",
                          f"{self.config.subnet}.{i+1}/24", "dev", f"vpeer-{ns}"], capture_output=True)

    def start_session(self, ns_name: str, username: str) -> bool:
        """Start a PPPoE session inside a netns."""
        start = time.time()
        try:
            result = subprocess.run(
                ["ip", "netns", "exec", ns_name,
                 "pppd", "call", "rnas-pppoe",
                 "user", username, "password", self.config.password,
                 "nodetach"],
                capture_output=True, text=True, timeout=15,
            )
            elapsed = time.time() - start
            ok = "succeeded" in result.stdout.lower()
            if ok:
                self.results["connected"] += 1
                self.results["times"].append(elapsed)
            else:
                self.results["failed"] += 1
                self.results["errors"].append(result.stderr[:200])
            return ok
        except subprocess.TimeoutExpired:
            self.results["failed"] += 1
            return False

    def wait_for_sessions(self, count: int, timeout: int = 60) -> bool:
        """Poll accel-cmd until session count reaches target."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                out = subprocess.run(
                    ["accel-cmd", "show", "stat"], capture_output=True, text=True, timeout=5
                ).stdout
                m = re.search(r"sessions:.*?active:\s*(\d+)", out, re.DOTALL)
                if m and int(m.group(1)) >= count:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def teardown(self):
        """Clean up all namespaces and bridge."""
        for ns in self.namespaces:
            subprocess.run(["ip", "netns", "del", ns], capture_output=True)
        subprocess.run(["ip", "link", "del", self.config.bridge_name], capture_output=True)
        # Terminate any lingering pppd processes
        subprocess.run(["pkill", "-f", "pppd.*rnas-pppoe"], capture_output=True)

    def run(self) -> dict:
        """Execute the full stress test and return results."""
        self.setup_network()
        interval = 1.0 / self.config.rate if self.config.rate > 0 else 0.1
        start_time = time.time()

        for i, ns in enumerate(self.namespaces):
            username = f"{self.config.username_prefix}{i+1}"
            self.start_session(ns, username)
            time.sleep(interval)
            if self.config.duration and time.time() - start_time > self.config.duration:
                break

        return {
            "total": self.config.cpe_count,
            "connected": self.results["connected"],
            "failed": self.results["failed"],
            "avg_time_ms": round(sum(self.results["times"]) / max(len(self.results["times"]), 1) * 1000, 1) if self.results["times"] else 0,
            "max_time_ms": round(max(self.results["times"]) * 1000, 1) if self.results["times"] else 0,
            "errors": self.results["errors"][:10],
        }
