#!/usr/bin/env python3
"""
RNAS Stress Test Engine — network namespace-based bulk CPE simulation.

Creates N virtual CPEs via Linux network namespaces, each running pppd to
simulate concurrent PPPoE sessions against accel-ppp.

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
    │          │ (master)        │    │
    │    accel-ppp iface (SUT)   │    │
    └────────────────────────────┘    │
    NOTE: bridging the accel-ppp interface into the bridge moves it out of
    its current netns context — on a production host this disconnects the
    management network. Use a dedicated test NIC (e.g. eth1) or a separate
    test host for full runs.

Usage:
    rnas-test stress --cpe-count 20 --bridge-ens33-off 1
    rnas-test stress --cpe-count 5 --dry-run
"""

import subprocess
import time
import json
import os
import re
import sys
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StressConfig:
    cpe_count: int = 20
    protocol: str = "pppoe"
    username_prefix: str = "testuser"
    password: str = "testpass"
    rate: float = 5.0
    duration: Optional[int] = None
    bridge_name: str = "rnas-br0"
    subnet: str = "10.99.0"
    # accel-ppp interface to attach to the bridge (empty = only create
    # bridge+veth topology for dry-run / infra validation)
    attach_iface: str = ""
    dry_run: bool = False
    peer_file: str = "rnas-pppoe"  # pppd peer name inside each netns


class StressEngine:
    """Manages bulk PPPoE session creation/destruction via Linux netns."""

    def __init__(self, config: StressConfig):
        self.config = config
        self.namespaces: list[str] = []
        self.results: dict = {"connected": 0, "failed": 0, "times": [], "errors": []}
        self._procs: list = []

    # -- network topology ---------------------------------------------------

    def _run(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run ip/network command; raise on failure when check=True."""
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if check and res.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd[:4])}... failed: {res.stderr.strip()[:200]}")
        return res

    def setup_network(self):
        """Create bridge and veth pairs for all CPEs.

        The accel-ppp interface (config.attach_iface) is added to the bridge
        AFTER the veths so PPPoE broadcasts reach the virtual CPEs. On a
        production host this moves that interface into the bridge (its IP
        moves too) — set attach_iface only on a dedicated test NIC.
        """
        self._run(["ip", "link", "add", self.config.bridge_name, "type", "bridge"])
        self._run(["ip", "link", "set", self.config.bridge_name, "up"])

        for i in range(self.config.cpe_count):
            ns = f"cpe-{i:03d}"
            self.namespaces.append(ns)
            self._run(["ip", "netns", "add", ns])
            self._run(["ip", "link", "add", f"veth-{ns}", "type", "veth", "peer", f"vpeer-{ns}"])
            self._run(["ip", "link", "set", f"vpeer-{ns}", "netns", ns])
            self._run(["ip", "link", "set", f"veth-{ns}", "master", self.config.bridge_name])
            self._run(["ip", "link", "set", f"veth-{ns}", "up"])
            self._run(["ip", "netns", "exec", ns, "ip", "link", "set", "lo", "up"])
            self._run(["ip", "netns", "exec", ns, "ip", "link", "set", f"vpeer-{ns}", "up"])
            self._run(["ip", "netns", "exec", ns, "ip", "addr", "add",
                       f"{self.config.subnet}.{i+1}/24", "dev", f"vpeer-{ns}"])

        if self.config.attach_iface:
            self._run(["ip", "link", "set", self.config.attach_iface, "master", self.config.bridge_name])
            self._run(["ip", "link", "set", self.config.attach_iface, "up"])
            print(f"[net] attached {self.config.attach_iface} to bridge {self.config.bridge_name}")

    # -- session management -------------------------------------------------

    def _check_pppd_peer(self, ns_name: str) -> bool:
        """Ensure the pppd peers file exists inside the netns (share host /etc/ppp)."""
        # netns shares the host filesystem for /etc — peers file is available
        # if present on the host.
        peer = Path("/etc/ppp/peers") / self.config.peer_file
        return peer.exists()

    def start_session(self, ns_name: str, username: str) -> bool:
        """Start a PPPoE session inside a netns (non-blocking, backgrounded).

        pppd runs with 'nodetach' so the netns exec stays alive; we spawn it
        with Popen and treat 'local IP address' in a short-lived capture as
        success. Because pppd keeps running, success is confirmed by polling
        accel-cmd for the session instead.
        """
        if not self._check_pppd_peer(ns_name):
            self.results["failed"] += 1
            self.results["errors"].append(f"{ns_name}: peer {self.config.peer_file} missing")
            return False

        cmd = [
            "ip", "netns", "exec", ns_name,
            "pppd", "call", self.config.peer_file,
            "user", username, "password", self.config.password,
            "nodetach", "logfile", f"/tmp/pppd-{ns_name}.log",
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._procs.append((ns_name, proc))
            return True
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"{ns_name}: {e}")
            return False

    def wait_for_sessions(self, count: int, timeout: int = 60) -> int:
        """Poll accel-cmd until active sessions reach count. Returns actual count."""
        deadline = time.time() + timeout
        last = 0
        while time.time() < deadline:
            try:
                out = subprocess.run(
                    ["accel-cmd", "show", "stat"], capture_output=True, text=True, timeout=5
                ).stdout
                m = re.search(r"sessions:.*?active:\s*(\d+)", out, re.DOTALL)
                if m:
                    last = int(m.group(1))
                    if last >= count:
                        return last
            except Exception:
                pass
            time.sleep(1)
        return last

    def teardown(self):
        """Stop all pppd, delete namespaces and bridge."""
        for ns, proc in self._procs:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._procs.clear()
        for ns in self.namespaces:
            subprocess.run(["ip", "netns", "del", ns], capture_output=True)
        subprocess.run(["ip", "link", "del", self.config.bridge_name], capture_output=True)
        self.namespaces.clear()

    # -- run ----------------------------------------------------------------

    def run(self) -> dict:
        """Execute the stress test and return results."""
        if self.config.dry_run:
            return self._dry_run()

        self.setup_network()
        start_time = time.time()
        interval = 1.0 / self.config.rate if self.config.rate > 0 else 0.1

        for i, ns in enumerate(self.namespaces):
            username = f"{self.config.username_prefix}{i+1}"
            self.start_session(ns, username)
            time.sleep(interval)
            if self.config.duration and time.time() - start_time > self.config.duration:
                break

        connected = self.wait_for_sessions(self.config.cpe_count, timeout=30)
        self.results["connected"] = connected

        result = {
            "total": self.config.cpe_count,
            "connected": connected,
            "failed": self.config.cpe_count - connected,
            "avg_time_ms": 0,
            "errors": self.results["errors"][:10],
        }
        return result

    def _dry_run(self) -> dict:
        """Validate topology creation without pppd dialing (safe on prod host)."""
        print(f"[dry-run] creating {self.config.cpe_count} netns + bridge {self.config.bridge_name}")
        self.setup_network()
        checks = {
            "bridge_exists": Path(f"/sys/class/net/{self.config.bridge_name}").exists(),
            "veth_count": len([p for p in Path('/sys/class/net').iterdir()
                               if p.name.startswith(f"veth-cpe-")]),
            "netns_ready": len(self.namespaces) == self.config.cpe_count,
        }
        self.teardown()
        checks["teardown_ok"] = not Path(f"/sys/class/net/{self.config.bridge_name}").exists()
        print(f"[dry-run] checks: {json.dumps(checks)}")
        return {"dry_run": True, "checks": checks}
