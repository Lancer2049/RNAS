#!/usr/bin/env python3
"""
RNAS Configuration Engine — reads /etc/rnas/ config tree, generates native service configs.

Usage:
    rnas-config generate accel-ppp [--root DIR] [--output FILE]
    rnas-config validate [--root DIR]
    rnas-config show [--root DIR] [SECTION]
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Import from module siblings (backward-compatible entry point)
from core import parse_config, interpolate_env, walk_config_tree
from config_ops import find_config_file, write_config_section
from generators import (
    generate_accel_ppp, generate_dnsmasq, generate_dhcp_relay,
    generate_firewall, generate_snmp, generate_qos,
    generate_ipsec, generate_wireguard, generate_openvpn,
    generate_dot1x, generate_hotspot, generate_ha,
    generate_vlan, generate_mac_auth, generate_ipv6,
    generate_gre, generate_ipip, generate_eoip, generate_vxlan,
    GEN_MAP,
)

# Re-export for backward compatibility (code importing from rnas_config)
__all__ = [
    "parse_config", "interpolate_env", "walk_config_tree",
    "find_config_file", "write_config_section",
    "generate_accel_ppp", "generate_dnsmasq", "generate_dhcp_relay",
    "generate_firewall", "generate_snmp", "generate_qos",
    "generate_ipsec", "generate_wireguard", "generate_openvpn",
    "generate_dot1x", "generate_hotspot", "generate_ha",
    "generate_vlan", "generate_mac_auth", "generate_ipv6",
    "generate_gre", "generate_ipip", "generate_eoip", "generate_vxlan",
    "GEN_MAP", "main",
]

DEFAULT_ROOT = "/etc/rnas"


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RNAS Configuration Engine")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Config root directory (default: {DEFAULT_ROOT})")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Show parsed config")
    gen = sub.add_parser("generate", help="Generate native service config")
    gen.add_argument("service", choices=sorted(GEN_MAP.keys()), help="Service to generate config for")
    gen.add_argument("--output", "-o", help="Output file (default: stdout)")

    sub.add_parser("validate", help="Validate config tree")
    snap = sub.add_parser("snapshot", help="Manage config snapshots")
    snap.add_argument("action", choices=["create", "list", "restore"], help="Snapshot action")
    snap.add_argument("--name", help="Snapshot name (for create/restore)")

    sc = sub.add_parser("scenario", help="Manage deployment scenarios")
    sc.add_argument("action", choices=["list", "apply"], help="Scenario action")
    sc.add_argument("name", nargs="?", help="Scenario name (for apply)")

    app = sub.add_parser("apply", help="Generate config and restart service")
    app.add_argument("service", choices=sorted([k for k in GEN_MAP if k not in ("gre", "ipip", "eoip", "vxlan", "ipv6", "vlan", "mac-auth")]), help="Service to apply")

    args = parser.parse_args()

    if args.command == "generate":
        config = walk_config_tree(Path(args.root))
        gen_func = GEN_MAP.get(args.service)
        if gen_func:
            result = gen_func(config)
        else:
            result = ""
        if args.output:
            Path(args.output).write_text(result)
        else:
            print(result)

    elif args.command == "show":
        config = walk_config_tree(Path(args.root))
        for section, values in sorted(config.items()):
            print(f"\n[{section}]")
            for k, v in sorted(values.items()):
                print(f"  {k} = {v}")

    elif args.command == "validate":
        root = Path(args.root)
        if not root.exists():
            print(f"ERROR: config root {args.root} does not exist", file=sys.stderr)
            sys.exit(1)
        files = list(root.rglob("*.conf"))
        errors = 0
        warnings = 0
        for f in files:
            try:
                config = parse_config(f.read_text())
            except Exception as e:
                print(f"ERROR: {f}: {e}", file=sys.stderr)
                errors += 1
                continue
            for section, values in config.items():
                for key, val in values.items():
                    if key in ("port", "auth_port", "acct_port") and val.isdigit():
                        p = int(val)
                        if p < 1 or p > 65535:
                            print(f"ERROR: {f}: [{section}] {key}={val} not in 1-65535", file=sys.stderr)
                            errors += 1
                    if key in ("auth_server", "acct_server", "nas_ip") and val:
                        import re
                        ip_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$", val)
                        if not ip_match:
                            print(f"WARNING: {f}: [{section}] {key}={val} does not look like IP", file=sys.stderr)
                            warnings += 1
        full_config = walk_config_tree(root)
        required = [("access.d.radius", "auth_host", "RADIUS auth server"),
                    ("access.d.radius", "secret", "RADIUS secret"),
                    ("access.d.pppoe", "interface", "PPPoE interface")]
        for section, key, desc in required:
            found = False
            for s, v in full_config.items():
                if s.startswith(section.replace(".d.", ".d.")) and key in v:
                    found = True; break
            if not found:
                print(f"WARNING: Required {desc} not set ({section}.{key})", file=sys.stderr)
                warnings += 1
        if errors:
            print(f"{errors} errors, {warnings} warnings", file=sys.stderr)
            sys.exit(1)
        print(f"OK: {len(files)} files valid, {warnings} warnings")

    elif args.command == "snapshot":
        snap_dir = Path("/etc/rnas/snapshots")
        if args.action == "create":
            name = args.name or f"snap-{datetime.now():%Y%m%d-%H%M%S}"
            (snap_dir / name).mkdir(parents=True, exist_ok=True)
            for f in Path(args.root).rglob("*.conf"):
                rel = f.relative_to(Path(args.root))
                target = snap_dir / name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f.read_text())
            print(f"Snapshot '{name}' created ({len(list((snap_dir/name).rglob('*.conf')))} files)")
        elif args.action == "list":
            if not snap_dir.exists():
                print("No snapshots")
            else:
                for d in sorted(snap_dir.iterdir()):
                    if d.is_dir():
                        cnt = len(list(d.rglob("*.conf")))
                        print(f"  {d.name} ({cnt} files)")
        elif args.action == "restore":
            if not args.name:
                print("ERROR: --name required for restore", file=sys.stderr); sys.exit(1)
            src = snap_dir / args.name
            if not src.exists():
                print(f"ERROR: snapshot '{args.name}' not found", file=sys.stderr); sys.exit(1)
            for f in src.rglob("*.conf"):
                rel = f.relative_to(src)
                (Path(args.root) / rel).write_text(f.read_text())
            print(f"Snapshot '{args.name}' restored")

    elif args.command == "scenario":
        sc_dir = Path("/etc/rnas/scenarios")
        if args.action == "list":
            if not sc_dir.exists():
                print("No scenarios")
            else:
                for f in sorted(sc_dir.glob("*.json")):
                    print(f"  {f.stem}")
        elif args.action == "apply":
            if not args.name:
                print("ERROR: scenario name required", file=sys.stderr); sys.exit(1)
            sc_file = sc_dir / f"{args.name}.json"
            if not sc_file.exists():
                print(f"ERROR: scenario '{args.name}' not found", file=sys.stderr); sys.exit(1)
            overrides = json.loads(sc_file.read_text())
            for key, val in overrides.get("config", {}).items():
                sec, opt = key.split(".", 1)
                conf_path = Path(args.root)
                for p in sec.split("."):
                    conf_path = conf_path / p
                if not conf_path.exists():
                    conf_path.parent.mkdir(parents=True, exist_ok=True)
                    conf_path.touch()
                lines = conf_path.read_text().splitlines() if conf_path.exists() else []
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith(f"{opt}="):
                        lines[i] = f"{opt}={val}"
                        found = True; break
                if not found:
                    lines.append(f"{opt}={val}")
                conf_path.write_text("\n".join(lines) + "\n")
            print(f"Scenario '{args.name}' applied")

    elif args.command == "apply":
        root = Path(args.root)
        config = walk_config_tree(root)
        svc = args.service
        if svc in GEN_MAP:
            out_dir = Path("/var/run/rnas")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{svc}.conf"
            result = GEN_MAP[svc](config)
            out_file.write_text(result)
            print(f"Generated {out_file}")
            svc_name = f"rnas-{svc}.service"
            ret = subprocess.run(["systemctl", "restart", svc_name], capture_output=True, text=True)
            if ret.returncode == 0:
                print(f"Restarted {svc_name}")
            else:
                print(f"Failed to restart {svc_name}: {ret.stderr}", file=sys.stderr)
        else:
            print(f"Unknown service: {svc}", file=sys.stderr)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
