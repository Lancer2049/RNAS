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

    existing_keys = set()
    insert_idx = header_idx + 1
    while insert_idx < len(lines):
        stripped = lines[insert_idx].strip()
        if stripped.startswith("[") and not stripped.startswith("#"):
            break
        m = re.match(r'^(\w[\w_]*)\s*=\s*', stripped)
        if m:
            key = m.group(1)
            if key in values:
                lines[insert_idx] = f"{key} = {values[key]}\n"
                existing_keys.add(key)
        insert_idx += 1

    for key, val in values.items():
        if key not in existing_keys:
            new_line = f"{key} = {val}\n"
            insert_point = header_idx + 1
            while insert_point < len(lines):
                s = lines[insert_point].strip()
                if s.startswith("[") and not s.startswith("#"):
                    break
                insert_point += 1
            lines.insert(insert_point, new_line)

    conf_file.write_text("".join(lines))
    return True
