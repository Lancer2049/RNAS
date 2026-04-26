#!/usr/bin/env python3
"""
RNAS Configuration Engine — reads /etc/rnas/ config tree, generates native service configs.

Usage:
    rnas-config generate accel-ppp [--root DIR] [--output FILE]
    rnas-config validate [--root DIR]
    rnas-config show [--root DIR] [SECTION]
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Optional

DEFAULT_ROOT = "/etc/rnas"

# ── INI-style parser ────────────────────────────────────────────────────────

def parse_config(text: str) -> Dict[str, Dict[str, str]]:
    """Parse INI-style config text. Supports [section "name"] and ${VAR} interpolation."""
    sections: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = re.match(r'^\[(\w+)(?:\s+"([^"]*)")?\]', stripped)
        if m:
            section = m.group(1)
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

# ── Tree walker ─────────────────────────────────────────────────────────────

def walk_config_tree(root: Path) -> Dict[str, Dict[str, str]]:
    """Walk /etc/rnas/ tree, parse all .conf files, merge into single config."""
    merged: Dict[str, Dict[str, str]] = {}
    for conf_file in sorted(root.rglob("*.conf")):
        rel = conf_file.relative_to(root)
        prefix = str(rel.parent).replace("/", ".").strip(".")
        text = conf_file.read_text()
        sections = parse_config(text)
        for name, values in sections.items():
            full_name = f"{prefix}.{name}" if prefix else name
            if full_name not in merged:
                merged[full_name] = {}
            merged[full_name].update(values)
    return merged

# ── Accel-PPP generator ─────────────────────────────────────────────────────

def generate_accel_ppp(config: Dict[str, Dict[str, str]]) -> str:
    """Generate native accel-ppp.conf from RNAS config tree."""
    out = []
    def w(line=""): out.append(line)

    def get_section(prefix: str) -> Dict[str, str]:
        return config.get(prefix, {})

    core = get_section("access.d.core")
    modules = get_section("access.d.modules")
    common = get_section("access.d.common")

    # Modules
    w("[modules]")
    mod_list = ["pppoe", "ipoe", "l2tp", "pptp", "sstp", "auth_pap", "auth_chap_md5",
                "auth_mschap_v1", "auth_mschap_v2", "radius", "ippool", "connlimit", "pppd_compat", "log_file"]
    for m in mod_list:
        if modules.get(m, "no") == "yes" or core.get(m, "no") == "yes":
            w(m)
    w()

    # Core
    w("[core]")
    if "log_file" in core: w(f"log-error={core['log_file']}")
    if "thread_count" in core: w(f"thread-count={core['thread_count']}")
    w("daemon=1")
    w()

    # Common
    w("[common]")
    if common.get("sid_source"): w(f"sid-source={common['sid_source']}")
    if common.get("check_ip") == "yes": w("check-ip=1")
    if common.get("max_sessions"): w(f"max-sessions={common['max_sessions']}")
    w()

    # PPP
    ppp = get_section("access.d.ppp")
    w("[ppp]")
    w("verbose=1")
    for k in ("min_mtu", "mtu", "mru", "acf", "pcf", "lcp_echo_interval", "lcp_echo_failure"):
        if k in ppp: w(f"{k.replace('_', '-')}={ppp[k]}")
    if ppp.get("ipv4") == "require": w("ipv4=require")
    if ppp.get("ipv6") == "deny": w("ipv6=deny")
    if ppp.get("unit_cache") == "yes": w("unit-cache=1")
    w()

    # RADIUS
    radius = get_section("access.d.server/primary")
    nas = get_section("access.d.nas")
    acct = get_section("access.d.accounting")
    dae = get_section("access.d.dae")

    w("[radius]")
    w("dictionary=/usr/share/accel-ppp/radius/dictionary")
    if nas.get("identifier"): w(f"nas-identifier={nas['identifier']}")
    if nas.get("ip_address"): w(f"nas-ip-address={nas['ip_address']}")
    if nas.get("gw_ip_address"): w(f"gw-ip-address={nas['gw_ip_address']}")

    server_parts = [
        radius.get("auth_host", ""),
        radius.get("secret", ""),
        f"auth-port={radius.get('auth_port', '1812')}",
        f"acct-port={radius.get('acct_port', '1813')}",
        f"req-limit={radius.get('req_limit', '50')}",
        f"fail-timeout={radius.get('fail_timeout', '0')}",
        f"max-fail={radius.get('max_fail', '10')}",
        f"weight={radius.get('weight', '1')}"
    ]
    w(f"server={','.join(filter(None, server_parts))}")

    if dae.get("enabled") == "yes":
        w(f"dae-server={dae.get('listen', '0.0.0.0:3799')},{dae.get('secret', 'testing123')}")
        if dae.get("allowed_clients"): w(f"dae-allowed={dae['allowed_clients']}")

    w("verbose=1")
    if radius.get("timeout"): w(f"timeout={radius['timeout']}")
    if radius.get("retries"): w(f"max-try={radius['retries']}")
    if acct.get("acct_timeout"): w(f"acct-timeout={acct['acct_timeout']}")
    if acct.get("acct_on") == "yes": w("acct-on=1")
    if acct.get("message_authenticator") == "yes": w("message-authenticator=1")
    w()

    # IP Pool
    pool = get_section("access.d.pool/default")
    cr = get_section("access.d.client_range")
    if cr.get("subnet"):
        w("[client-ip-range]")
        w(f"{cr['subnet']}")
        w()
    w("[ip-pool]")
    if pool.get("gateway"): w(f"gw-ip-address={pool['gateway']}")
    if pool.get("attr"): w(f"attr={pool['attr']}")
    if pool.get("range"): w(pool["range"])
    w()

    # Protocols
    for proto in [("pppoe", "pppoe"), ("pptp", "pptp"), ("l2tp", "l2tp"), ("sstp", "sstp"), ("ipoe", "ipoe")]:
        pconf = get_section(f"access.d.{proto[1]}")
        if proto[0] == "ipoe" and pconf.get("enabled") != "yes":
            continue
        w(f"[{proto[1]}]")
        w("verbose=1")
        if pconf.get("interface"): w(f"interface={pconf['interface']}")
        if pconf.get("ac_name"): w(f"ac-name={pconf['ac_name']}")
        if pconf.get("service_name"): w(f"service-name={pconf['service_name']}")
        if pconf.get("called_sid"): w(f"called-sid={pconf['called_sid']}")
        if pconf.get("port"): w(f"port={pconf['port']}")
        if pconf.get("accept"): w(f"accept={pconf['accept']}")
        if proto[0] == "l2tp": w("dictionary=/usr/share/accel-ppp/l2tp/dictionary")
        w()

    # CLI
    cli = get_section("access.d.cli")
    w("[cli]")
    w("verbose=1")
    if cli.get("tcp"): w(f"tcp={cli['tcp']}")
    w()

    # Log
    w("[log]")
    w("log-file=/var/log/accel-ppp/accel-ppp.log")
    w("level=3")
    w("copy=1")
    w()

    # PPPoE compat
    w("[pppd-compat]")
    w("verbose=1")
    w()

    return "\n".join(out)


def generate_dnsmasq(config: Dict[str, Dict[str, str]]) -> str:
    dhcp = config.get("network.d.dhcp/dhcp lan", {})
    dns = config.get("network.d.dhcp/dhcp_option dns", {})
    iface = config.get("network.d.interface/lan", {})

    out = []
    out.append("# Generated by rnas-config — do not edit")
    out.append("")

    iface_name = iface.get("device", "br-lan")
    out.append(f"interface={iface_name}")

    start = dhcp.get("start", "100")
    limit = dhcp.get("limit", "100")
    ip = iface.get("ipaddr", "192.168.100.1")
    netmask = iface.get("netmask", "255.255.255.0")
    lease = dhcp.get("leasetime", "12h")

    # Calculate DHCP range from base IP + start
    ip_parts = ip.rsplit(".", 1)
    range_start = f"{ip_parts[0]}.{start}" if len(ip_parts) == 2 else ip
    end_ip = int(start) + int(limit) - 1
    range_end = f"{ip_parts[0]}.{end_ip}" if len(ip_parts) == 2 else ip

    out.append(f"dhcp-range={range_start},{range_end},{netmask},{lease}")

    dns_list = dns.get("list", "8.8.8.8,8.8.4.4")
    out.append(f"dhcp-option=6,{dns_list}")

    out.append("no-resolv")
    out.append("server=8.8.8.8")
    out.append("server=8.8.4.4")
    out.append("")

    return "\n".join(out)

A_NET = "192.168.100.0/24"

def generate_firewall(config: Dict[str, Dict[str, str]]) -> str:
    zone = config.get("network.d.zone/nas", {})
    rules = {}
    for k, v in config.items():
        if k.startswith("network.d.rule/"):
            rules[k] = v

    out = []
    out.append("# Generated by rnas-config — do not edit")
    out.append("flush ruleset")
    out.append("")

    # Base chain setup
    out.append("table inet rnas {")
    out.append("    chain input {")
    out.append("        type filter hook input priority 0; policy drop;")
    out.append("        iif lo accept")
    out.append("        ct state established,related accept")
    out.append("    }")
    out.append("")
    out.append("    chain forward {")
    out.append("        type filter hook forward priority 0; policy drop;")
    out.append(f"        ip saddr {A_NET} accept")
    out.append("    }")
    out.append("")

    # Allow RADIUS + CoA
    out.append("    chain output {")
    out.append("        type filter hook output priority 0; policy accept;")
    out.append("    }")
    out.append("}")

    return "\n".join(out)


def generate_snmp(config: Dict[str, Dict[str, str]]) -> str:
    snmp = config.get("snmp", {})
    nf = config.get("netflow", {})
    sl = config.get("syslog", {})

    out = []
    out.append("# Generated by rnas-config — do not edit")
    out.append("")
    if snmp.get("enabled") == "yes":
        out.append(f"agentaddress {snmp.get('listen', '0.0.0.0:161')}")
        out.append(f"rocommunity {snmp.get('community', 'public')}")
        out.append(f"syslocation {snmp.get('location', 'NAS Lab')}")
        out.append(f"syscontact {snmp.get('contact', 'admin@rnas.local')}")
    out.append("")

    return "\n".join(out)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RNAS Configuration Engine")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Config root directory (default: {DEFAULT_ROOT})")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Show parsed config")
    gen = sub.add_parser("generate", help="Generate native service config")
    gen.add_argument("service", choices=["accel-ppp", "dnsmasq", "firewall", "snmp"], help="Service to generate config for")
    gen.add_argument("--output", "-o", help="Output file (default: stdout)")

    sub.add_parser("validate", help="Validate config tree")

    args = parser.parse_args()

    if args.command == "generate":
        config = walk_config_tree(Path(args.root))
        if args.service == "accel-ppp":
            result = generate_accel_ppp(config)
        elif args.service == "dnsmasq":
            result = generate_dnsmasq(config)
        elif args.service == "firewall":
            result = generate_firewall(config)
        elif args.service == "snmp":
            result = generate_snmp(config)
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
        for f in files:
            try:
                parse_config(f.read_text())
            except Exception as e:
                print(f"ERROR: {f}: {e}", file=sys.stderr)
                errors += 1
        if errors:
            print(f"{errors} config files have errors", file=sys.stderr)
            sys.exit(1)
        print(f"OK: {len(files)} config files valid")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
