#!/usr/bin/env python3
"""RADIUS Dictionary Parser — Parse FreeRADIUS-format dictionary files"""
import os, re
from pathlib import Path
from typing import Dict, List, Optional

DICT_DIR = Path("/etc/rnas/dictionary")

TYPE_MAP = {
    "integer": "integer",
    "string": "string",
    "ipaddr": "ipaddr",
    "date": "date",
    "octets": "octets",
    "ifid": "ifid",
    "ipv6addr": "ipv6addr",
    "ipv6prefix": "ipv6prefix",
}


def parse_dictionary(text: str, vendor_info: dict = None) -> dict:
    """Parse a single dictionary file. Returns {name: {vendor, id, type}}"""
    entries = {}
    current_vendor = vendor_info or {"name": "IETF", "id": 0}
    in_vendor = False
    vendor_name = current_vendor.get("name", "IETF")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # VENDOR directive
        m = re.match(r"VENDOR\s+(\S+)\s+(\d+)", stripped, re.IGNORECASE)
        if m:
            vendor_name = m.group(1)
            vendor_id = int(m.group(2))
            current_vendor = {"name": vendor_name, "id": vendor_id}
            in_vendor = False
            continue

        # BEGIN-VENDOR
        if re.match(r"BEGIN-VENDOR\s+(\S+)", stripped, re.IGNORECASE):
            in_vendor = True
            continue

        # END-VENDOR
        if re.match(r"END-VENDOR\s+(\S+)", stripped, re.IGNORECASE):
            in_vendor = False
            vendor_name = current_vendor.get("name", "IETF")
            continue

        # ATTRIBUTE directive
        m = re.match(
            r"ATTRIBUTE\s+(\S+)\s+(\d+)\s+(\S+)", stripped, re.IGNORECASE
        )
        if m:
            name = m.group(1)
            attr_id = int(m.group(2))
            attr_type = m.group(3).lower()
            if attr_type in TYPE_MAP:
                entries[name] = {
                    "vendor": vendor_name,
                    "vendor_id": current_vendor.get("id", 0),
                    "id": attr_id,
                    "type": TYPE_MAP[attr_type],
                }

    return entries


def load_all(dict_dir: str = None) -> dict:
    """Load all dictionary files into a flat dict."""
    if dict_dir is None:
        dict_dir = DICT_DIR
    all_entries = {}
    dir_path = Path(dict_dir)

    if not dir_path.exists():
        return all_entries

    for f in sorted(dir_path.iterdir()):
        if f.is_file() and f.suffix != ".py" and not f.name.startswith("."):
            text = f.read_text()
            entries = parse_dictionary(text)
            all_entries.update(entries)

    return all_entries


def search(query: str, dict_dir: str = None) -> List[dict]:
    """Search dictionary by partial attribute name."""
    all_entries = load_all(dict_dir)
    results = []
    q = query.lower()
    for name, info in all_entries.items():
        if q in name.lower() or q in info.get("vendor", "").lower():
            results.append({"name": name, **info})
    results.sort(key=lambda x: x["name"])
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        entries = load_all()
        for name in sorted(entries.keys()):
            e = entries[name]
            print(f"{e['vendor']:12s}  {e['id']:5d}  {e['type']:10s}  {name}")
    else:
        print(f"Loaded {len(load_all())} RADIUS attributes")
