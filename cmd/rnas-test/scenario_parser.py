"""
YAML Scenario DSL Parser — Phase 3-B.

Parses declarative test scenarios with topology, actions, and assertions.
Outputs an AST that the execution engine can run.

Format:
    name: PPPoE Batch Stress Test
    topology:
      cpe_count: 100
      protocol: pppoe
    actions:
      - command: connect
        target: all
        rate: 5/s
      - command: assert
        checks:
          - sessions_active == 100
    report:
      format: [junit, json]
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Scenario:
    name: str
    description: str = ""
    topology: dict = field(default_factory=dict)
    actions: list[dict] = field(default_factory=list)
    report: dict = field(default_factory=dict)


def parse_scenario(path: Path) -> Scenario:
    """Parse a YAML scenario file into a Scenario object."""
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Scenario must be a dict, got {type(data)}")

    return Scenario(
        name=data.get("name", path.stem),
        description=data.get("description", ""),
        topology=data.get("topology", {}),
        actions=data.get("actions", []),
        report=data.get("report", {}),
    )


def validate_scenario(scenario: Scenario) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors = []
    valid_commands = {"connect", "disconnect", "wait", "assert"}
    for i, action in enumerate(scenario.actions):
        cmd = action.get("command", "")
        if cmd not in valid_commands:
            errors.append(f"Action[{i}]: unknown command '{cmd}' (valid: {valid_commands})")
        if cmd == "wait" and "timeout" not in action and "condition" not in action:
            errors.append(f"Action[{i}]: 'wait' requires 'timeout' or 'condition'")
        if cmd == "assert" and "checks" not in action:
            errors.append(f"Action[{i}]: 'assert' requires 'checks' list")
    return errors


# Define the scenario format as JSON Schema for documentation
SCHEMA = {
    "type": "object",
    "required": ["name", "topology", "actions"],
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "topology": {
            "type": "object",
            "properties": {
                "cpe_count": {"type": "integer"},
                "protocol": {"type": "string", "enum": ["pppoe", "pptp", "l2tp", "sstp"]},
                "rate": {"type": "string", "pattern": r"^\d+/s$"},
            },
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "enum": ["connect", "disconnect", "wait", "assert"]},
                    "target": {"type": "string"},
                    "rate": {"type": "string"},
                    "timeout": {"type": "string"},
                    "condition": {"type": "object"},
                    "checks": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "report": {
            "type": "object",
            "properties": {
                "format": {"type": "array", "items": {"type": "string", "enum": ["junit", "html", "json"]}},
                "output": {"type": "string"},
            },
        },
    },
}
