# ── INI-style parser ────────────────────────────────────────────────────────

import os
import re
from pathlib import Path
from typing import Dict, Optional

def parse_config(text: str) -> Dict[str, Dict[str, str]]:
    """Parse INI-style config text. Supports [section] and [section/name] headers."""
    sections: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = re.match(r'^\[([\w/]+)(?:\s+"([^"]*)")?\]\s*$', stripped)
        if m:
            section = m.group(1).replace("/", "/")
            name = m.group(2)
            current = f"{section}/{name}" if name else section
            if current not in sections:
                sections[current] = {}
            continue

        m = re.match(r'^(\w[\w_]*)\s*=\s*(.*)', stripped)
        if m and current:
            key = m.group(1)
            val = interpolate_env(m.group(2).strip())
            sections[current][key] = val
    return sections

def interpolate_env(val: str) -> str:
    """Resolve ${VAR:-default} patterns using environment variables."""
    def _replace(m: re.Match) -> str:
        inner = m.group(1)
        if ":-" in inner:
            var, default = inner.split(":-", 1)
            return os.environ.get(var, default)
        return os.environ.get(inner, "")
    return re.sub(r'\$\{([^}]+)\}', _replace, val)

def walk_config_tree(root: Path) -> Dict[str, Dict[str, str]]:
    merged: Dict[str, Dict[str, str]] = {}
    # Skip snapshot/backup dirs so historical configs are not treated as active
    ignored_dirs = {"snapshots", "backup", "archive", "bak"}
    for conf_file in sorted(root.rglob("*.conf")):
        if any(part in ignored_dirs for part in conf_file.parts):
            continue
        rel = conf_file.relative_to(root)
        prefix = str(rel.parent).replace("/", ".").strip(".")
        if not prefix:
            prefix = rel.stem
        text = conf_file.read_text()
        sections = parse_config(text)
        for name, values in sections.items():
            full_name = f"{prefix}.{name}" if prefix else name
            if full_name not in merged:
                merged[full_name] = {}
            merged[full_name].update(values)
    return merged
