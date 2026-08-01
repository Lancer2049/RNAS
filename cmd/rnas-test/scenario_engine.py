#!/usr/bin/env python3
"""
RNAS Scenario Execution Engine — Phase 3-B.

Runs a parsed Scenario AST:
  connect    → dial N virtual CPEs (netns pppd)
  wait       → poll until condition or timeout
  assert     → evaluate check expressions against the live state
  disconnect → tear down sessions

Outputs results in JSON and optional JUnit XML.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from stress_engine import StressEngine, StressConfig
from scenario_parser import Scenario, parse_scenario, validate_scenario


# ---------------------------------------------------------------------------
# State providers
# ---------------------------------------------------------------------------

def get_session_state() -> dict:
    """Collect current session/radius state via accel-cmd."""
    import subprocess
    state = {"sessions_active": 0, "sessions_by_proto": {}, "radius_acct_start": 0}
    try:
        out = subprocess.run(["accel-cmd", "show", "stat"], capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"sessions:.*?active:\s*(\d+)", out, re.DOTALL)
        if m:
            state["sessions_active"] = int(m.group(1))
    except Exception:
        pass
    return state


# ---------------------------------------------------------------------------
# Assertion engine
# ---------------------------------------------------------------------------

def _eval_check(check: str, state: dict) -> tuple[bool, str]:
    """Evaluate a single check like 'sessions_active == 100'."""
    for op, fn in [(">=", lambda a, b: a >= b),
                   ("<=", lambda a, b: a <= b),
                   ("==", lambda a, b: a == b),
                   ("!=", lambda a, b: a != b),
                   (">", lambda a, b: a > b),
                   ("<", lambda a, b: a < b)]:
        if op in check:
            left, _, right = check.partition(op)
            key = left.strip()
            try:
                val = float(right.strip())
            except ValueError:
                val = right.strip().strip("'\"")
            actual = state.get(key, state.get("sessions_by_proto", {}).get(key))
            if actual is None:
                return False, f"{key} not in state"
            try:
                ok = fn(float(actual), val)
            except (TypeError, ValueError):
                ok = fn(actual, val)
            return ok, f"{key}{op}{right.strip()} (actual={actual})"
    return False, f"unsupported check: {check}"


def run_assertions(checks: list[str], state: dict) -> list[dict]:
    results = []
    for c in checks:
        ok, detail = _eval_check(c, state)
        results.append({"check": c, "ok": ok, "detail": detail})
    return results


# ---------------------------------------------------------------------------
# Action executor
# ---------------------------------------------------------------------------

class ScenarioRunner:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.engine: Optional[StressEngine] = None
        self.step_results: list[dict] = []
        self.state: dict = {}

    def _start_engine(self):
        topo = self.scenario.topology
        self.engine = StressEngine(StressConfig(
            cpe_count=int(topo.get("cpe_count", 10)),
            protocol=topo.get("protocol", "pppoe"),
            username_prefix=topo.get("credentials", {}).get("username_prefix", "testuser"),
            password=topo.get("credentials", {}).get("password", "testpass"),
        ))

    def run(self) -> dict:
        start = time.time()
        for i, action in enumerate(self.scenario.actions, 1):
            cmd = action.get("command")
            result = self._run_action(i, action)
            self.step_results.append(result)
            if not result["ok"] and cmd == "assert":
                break  # assertion failure is fatal
        return {
            "scenario": self.scenario.name,
            "duration_s": round(time.time() - start, 2),
            "passed": all(r["ok"] for r in self.step_results),
            "steps": self.step_results,
        }

    def _run_action(self, idx: int, action: dict) -> dict:
        cmd = action.get("command")
        name = action.get("name", cmd)
        try:
            if cmd == "connect":
                return self._connect(idx, name, action)
            if cmd == "wait":
                return self._wait(idx, name, action)
            if cmd == "assert":
                return self._assert(idx, name, action)
            if cmd == "disconnect":
                return self._disconnect(idx, name, action)
            return {"step": idx, "name": name, "command": cmd, "ok": False, "error": f"unknown command {cmd}"}
        except Exception as e:
            return {"step": idx, "name": name, "command": cmd, "ok": False, "error": str(e)}

    def _connect(self, idx, name, action):
        if not self.engine:
            self._start_engine()
        self.engine.setup_network()
        target = int(action.get("target", "all") == "all" and self.engine.config.cpe_count
                     or action.get("target", self.engine.config.cpe_count))
        for i in range(min(target, self.engine.config.cpe_count)):
            ns = self.engine.namespaces[i]
            self.engine.start_session(ns, f"{self.engine.config.username_prefix}{i+1}")
        self.state = get_session_state()
        return {"step": idx, "name": name, "command": "connect", "ok": True, "detail": f"dialed {target}"}

    def _wait(self, idx, name, action):
        timeout = _parse_duration(action.get("timeout", "30s"))
        cond = action.get("condition", {})
        deadline = time.time() + timeout
        self.state = get_session_state()
        while time.time() < deadline:
            self.state = get_session_state()
            if all(self.state.get(k) == v for k, v in cond.items()):
                return {"step": idx, "name": name, "command": "wait", "ok": True,
                        "detail": f"condition met: {self.state}"}
            time.sleep(1)
        return {"step": idx, "name": name, "command": "wait", "ok": False,
                "detail": f"timeout after {timeout}s; state={self.state}"}

    def _assert(self, idx, name, action):
        self.state = get_session_state()
        checks = run_assertions(action.get("checks", []), self.state)
        ok = all(c["ok"] for c in checks)
        return {"step": idx, "name": name, "command": "assert", "ok": ok, "checks": checks}

    def _disconnect(self, idx, name, action):
        if self.engine:
            self.engine.teardown()
        self.state = get_session_state()
        return {"step": idx, "name": name, "command": "disconnect", "ok": True,
                "detail": f"active={self.state.get('sessions_active', 0)}"}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _parse_duration(s: str) -> int:
    """Parse '30s', '2m', '60' into seconds."""
    s = str(s).strip()
    m = re.match(r"^(\d+)([sm]?)$", s)
    if m:
        val, unit = int(m.group(1)), m.group(2)
        return val * 60 if unit == "m" else val
    try:
        return int(s)
    except ValueError:
        return 30


def to_junit_xml(result: dict) -> str:
    """Render scenario result as JUnit XML for CI integration."""
    ts = datetime.now().isoformat()
    passed = "1" if result["passed"] else "0"
    failed = "0" if result["passed"] else "1"
    steps = "\n".join(
        f'    <testcase name="{s["name"]}" classname="scenario"><system-out>{s.get("detail", "")}</system-out></testcase>'
        if s["ok"] else
        f'    <testcase name="{s["name"]}" classname="scenario"><failure message="{s.get("error", "")}">{s.get("detail", "")}</failure></testcase>'
        for s in result["steps"]
    )
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<testsuite name="{result["scenario"]}" tests="{len(result["steps"])}" failures="{failed}" '
            f'timestamp="{ts}" time="{result["duration_s"]}">\n{steps}\n</testsuite>')


def run_scenario_file(path: Path, format: str = "json") -> dict:
    scenario = parse_scenario(path)
    errors = validate_scenario(scenario)
    if errors:
        raise ValueError("; ".join(errors))
    runner = ScenarioRunner(scenario)
    result = runner.run()
    if format == "junit":
        result["junit_xml"] = to_junit_xml(result)
    return result
