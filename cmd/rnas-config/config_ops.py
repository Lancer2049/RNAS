import re
from pathlib import Path
from typing import Dict, Optional, List


def find_config_file(root: Path, section_name: str) -> Optional[Path]:
    """Find which .conf file contains a given config section."""
    ignored_dirs = {"snapshots", "backup", "archive", "bak"}
    for conf_file in sorted(root.rglob("*.conf")):
        if any(part in ignored_dirs for part in conf_file.parts):
            continue
        text = conf_file.read_text()
        base = section_name
        name_part = ""
        if "/" in section_name:
            base, name_part = section_name.split("/", 1)
        pattern = rf'^\[{re.escape(base)}(\s+"{re.escape(name_part)}")?\]'
        if re.search(pattern, text, re.MULTILINE):
            return conf_file
    return None


def write_config_section(root: Path, section_name: str, values: Dict[str, str]) -> bool:
    """Write key=value pairs into a config section. Returns True on success."""
    conf_file = find_config_file(root, section_name)
    if not conf_file:
        return False

    text = conf_file.read_text()
    lines = text.splitlines(keepends=True)

    base = section_name
    name_part = ""
    if "/" in section_name:
        base, name_part = section_name.split("/", 1)

    header_pattern = rf'^\[{re.escape(base)}(\s+"{re.escape(name_part)}")?\]'
    header_idx = -1
    for i, line in enumerate(lines):
        if re.match(header_pattern, line.strip()):
            header_idx = i
            break
    if header_idx < 0:
        return False

    # Remove ALL existing occurrences of the target keys within the section
    # (a key may appear more than once from prior partial writes).
    key_lines_to_remove = set()
    j = header_idx + 1
    while j < len(lines):
        stripped = lines[j].strip()
        if stripped.startswith("[") and not stripped.startswith("#"):
            break
        m = re.match(r'^(\w[\w_]*)\s*=\s*', stripped)
        if m and m.group(1) in values:
            key_lines_to_remove.add(j)
        j += 1
    if key_lines_to_remove:
        lines = [l for idx, l in enumerate(lines) if idx not in key_lines_to_remove]

    # Insert the new key=value pairs right after the section header
    insert_at = header_idx + 1
    for key, val in values.items():
        lines.insert(insert_at, f"{key} = {val}\n")
        insert_at += 1

    conf_file.write_text("".join(lines))
    return True
