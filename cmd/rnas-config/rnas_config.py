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
import json
import argparse
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

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
    merged: Dict[str, Dict[str, str]] = {}
    for conf_file in sorted(root.rglob("*.conf")):
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
                "auth_mschap_v1", "auth_mschap_v2", "radius", "ippool", "connlimit", "pppd_compat", "log_file", "vlan-mon"]
    for m in mod_list:
        if modules.get(m, "no") == "yes" or core.get(m, "no") == "yes":
            w(m)
    w()

    # Core
    w("[core]")
    if "log_file" in core: w(f"log-error={core['log_file']}")
    if "thread_count" in core: w(f"thread-count={core['thread_count']}")
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
    for k in ("min_mtu", "mtu", "mru", "acf", "pcf", "lcp_echo_interval", "lcp_echo_failure", "iprange"):
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

    # Client IP Range (for L2TP/PPTP/SSTP tunnel source filtering)
    cr = get_section("access.d.client_range")
    w("[client-ip-range]")
    if cr.get("subnet"):
        w(f"{cr['subnet']}")
    else:
        w("0.0.0.0/0")
    w()

    # IP Pool
    pool = get_section("access.d.pool/default")
    w("[ip-pool]")
    if pool.get("gateway"): w(f"gw-ip-address={pool['gateway']}")
    if pool.get("attr"): w(f"attr={pool['attr']}")
    if pool.get("range"):
        w(pool["range"])
        w(f"{pool['range']},name=default")

    # Protocols
    for proto in [("pppoe", "pppoe"), ("pptp", "pptp"), ("l2tp", "l2tp"), ("sstp", "sstp"), ("ipoe", "ipoe")]:
        pconf = get_section(f"access.d.{proto[1]}")
        if proto[0] == "ipoe" and pconf.get("enabled") != "yes":
            continue
        w(f"[{proto[1]}]")
        verbose_val = pconf.get("verbose", "1")
        if verbose_val == "1": w("verbose=1")
        elif verbose_val: w(f"verbose={verbose_val}")
        if pconf.get("interface"):
            iface = pconf['interface']
            if proto[0] == "ipoe" and pconf.get("interface_opts"):
                iface += pconf['interface_opts']
            w(f"interface={iface}")
        if pconf.get("ac_name"): w(f"ac-name={pconf['ac_name']}")
        if pconf.get("service_name"): w(f"service-name={pconf['service_name']}")
        if pconf.get("bind"): w(f"bind={pconf['bind']}")
        if pconf.get("port"): w(f"port={pconf['port']}")
        if pconf.get("accept"): w(f"accept={pconf['accept']}")
        if pconf.get("ssl_pemfile"): w(f"ssl-pemfile={pconf['ssl_pemfile']}")
        if pconf.get("ip_pool"): w(f"ip-pool={pconf['ip_pool']}")
        if pconf.get("opt_src"): w(f"opt-src={pconf['opt_src']}")
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

def generate_dhcp_relay(config: Dict[str, Dict[str, str]]) -> str:
    relay = config.get("network.d.relay", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if relay.get("enabled") != "yes":
        out.append("# DHCP Relay disabled")
        return "\n".join(out)
    upstream = relay.get("upstream", "192.168.0.202")
    giaddr = relay.get("giaddr", "192.168.100.1")
    iface = relay.get("interface", "ens33")
    out.append(f"[relay]")
    out.append(f"enabled=yes")
    out.append(f"upstream={upstream}:67")
    out.append(f"giaddr={giaddr}")
    out.append(f"interface={iface}")
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
    snmp = config.get("monitor.snmp", config.get("snmp", {}))
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


def generate_qos(config: Dict[str, Dict[str, str]]) -> str:
    qos = config.get("qos.global", {})
    dc = config.get("qos.default_class", {})
    pu = config.get("qos.per_user", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if qos.get("enabled") != "yes":
        out.append("# QoS disabled")
        return "\n".join(out)
    iface = qos.get("interface", "ens33")
    algo = qos.get("algorithm", "cake")
    rate = dc.get("rate", "100mbit")
    out.append(f"# QoS: {algo} on {iface}, default rate {rate}")
    out.append("")
    out.append(f"tc qdisc add dev {iface} root handle 1: {algo} bandwidth {rate}")
    if pu.get("enabled") == "yes":
        dr = pu.get("default_rate", "10mbit")
        out.append(f"# Per-user shaping: RADIUS attr {pu.get('radius_attr', 'WISPr-Bandwidth-Max-Up')} → tc class")
        out.append(f"# To enable per-user: create HTB classes + iptables MARK per user IP")
    out.append("")
    return "\n".join(out)


def generate_ipsec(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("vpn.d.ipsec", config.get("vpn.d.global", {}))
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# IPsec disabled")
        return "\n".join(out)
    out.append("config setup")
    out.append("    charondebug=\"cfg 2\"")
    out.append("")
    out.append("conn rnas-default")
    out.append(f"    left=%defaultroute")
    out.append(f"    leftauth={g.get('auth', 'psk')}")
    out.append("    right=%any")
    out.append("    auto=add")
    out.append("")
    return "\n".join(out)


def generate_wireguard(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("vpn.d.wireguard", config.get("vpn.d.global", {}))
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# WireGuard disabled")
        return "\n".join(out)
    out.append("[Interface]")
    out.append(f"ListenPort = {g.get('listen_port', '51820')}")
    out.append("")
    for k, v in config.items():
        if k.startswith("vpn.d.peer/"):
            out.append(f"# Peer: {k.rsplit('/', 1)[-1]}")
            if v.get("public_key"): out.append(f"PublicKey = {v['public_key']}")
            if v.get("allowed_ips"): out.append(f"AllowedIPs = {v['allowed_ips']}")
            out.append("")
    return "\n".join(out)


def generate_openvpn(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("vpn.d.openvpn", config.get("vpn.d.global", {}))
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# OpenVPN disabled")
        return "\n".join(out)
    out.append(f"port {g.get('port', '1194')}")
    out.append(f"proto {g.get('proto', 'udp')}")
    out.append(f"dev {g.get('dev', 'tun')}")
    out.append("server 10.8.0.0 255.255.255.0")
    if g.get("auth") == "radius":
        out.append("plugin /usr/lib/openvpn/radiusplugin.so /etc/openvpn/radius.conf")
    out.append("")
    return "\n".join(out)


def generate_dot1x(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("wireless.d.dot1x", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# 802.1X disabled")
        return "\n".join(out)
    out.append(f"interface={g.get('interface', 'ens33')}")
    out.append("driver=wired")
    out.append("ieee8021x=1")
    out.append("eapol_version=2")
    out.append(f"auth_server_addr={g.get('auth_server', '192.168.0.202')}")
    out.append(f"auth_server_port={g.get('auth_port', '1812')}")
    out.append(f"auth_server_shared_secret={g.get('auth_secret', 'testing123')}")
    out.append("eap_server=0")
    out.append(f"nas_identifier={g.get('nas_identifier', 'rnas-dot1x')}")
    # EAP methods are configured in FreeRADIUS, not hostapd
    if g.get("ca_cert"): out.append(f"ca_cert={g['ca_cert']}")
    if g.get("server_cert"): out.append(f"server_cert={g['server_cert']}")
    if g.get("private_key"): out.append(f"private_key={g['private_key']}")
    out.append("")
    return "\n".join(out)

def generate_hotspot(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("hotspot.global", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# Hotspot disabled")
        return "\n".join(out)
    out.append(f"dhcpif {g.get('dhcp_if', g.get('interface', 'br-lan'))}")
    out.append(f"net {g.get('net', '192.168.182.0/24')}")
    out.append(f"uamserver {g.get('uam_server', 'https://hotspot.rnas.dev')}")
    out.append(f"radiusserver1 {g.get('radius_server', '192.168.0.85')}")
    out.append(f"radiussecret {g.get('radius_secret', 'testing123')}")
    out.append("")
    return "\n".join(out)


def generate_ha(config: Dict[str, Dict[str, str]]) -> str:
    g = config.get("ha.global", {})
    vrrp = config.get("ha.vrrp/instance_1", {})
    vip = config.get("ha.vip", {})
    auth = config.get("ha.auth", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# HA disabled")
        return "\n".join(out)
    out.append("vrrp_instance rnas_ha {")
    out.append(f"    state MASTER")
    out.append(f"    interface {vrrp.get('interface', 'ens33')}")
    out.append(f"    virtual_router_id {vrrp.get('virtual_router_id', '51')}")
    out.append(f"    priority {vrrp.get('priority', '100')}")
    out.append(f"    advert_int {vrrp.get('advert_interval', '1')}")
    out.append("    authentication {")
    out.append(f"        auth_type {auth.get('type', 'PASS')}")
    out.append(f"        auth_pass {auth.get('password', 'changeme')}")
    out.append("    }")
    for addr in vip.get("addresses", "").split(","):
        addr = addr.strip()
        if addr: out.append(f"    virtual_ipaddress {{ {addr} }}")
    out.append("}")
    out.append("")
    return "\n".join(out)


def generate_vlan(config: Dict[str, Dict[str, str]]) -> str:
    """Generate vlan-mon config for per-user VLAN assignment via RADIUS."""
    g = config.get("network.d.vlan", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# VLAN per user disabled")
        return "\n".join(out)
    parent = g.get("interface", "ens33")
    vrange = g.get("vlan_range", "2-4094")
    out.append(f"vlan-mon={parent},{vrange}")
    if g.get("vlan_name"): out.append(f"vlan-name={g['vlan_name']}")
    if g.get("pppoe_pattern"): out.append(f"# PPPoE VLAN: use interface={g['pppoe_pattern']} in [pppoe] section")
    if g.get("ipoe_start"): out.append(f"# IPoE VLAN: use start={g['ipoe_start']} in [ipoe] section")
    out.append("")
    return "\n".join(out)


def generate_mac_auth(config: Dict[str, Dict[str, str]]) -> str:
    """Generate MAC authentication config — bypasses PPPoE for known MACs via RADIUS."""
    g = config.get("access.d.mac_auth", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# MAC Auth disabled")
        return "\n".join(out)
    out.append(f"interface={g.get('interface', 'ens33')}")
    out.append("mode=L2")
    out.append("start=dhcpv4")
    out.append(f"username={g.get('username_format', 'mac')}")
    out.append(f"nas_identifier={g.get('nas_identifier', 'rnas-mac-auth')}")
    if g.get("vlan"): out.append(f"vlan={g['vlan']}")
    if g.get("ip_pool"): out.append(f"ip-pool={g['ip_pool']}")
    out.append("")
    return "\n".join(out)


def generate_ipv6(config: Dict[str, Dict[str, str]]) -> str:
    """Generate IPv6 dual-stack config for accel-ppp."""
    g = config.get("network.d.ipv6", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# IPv6 disabled")
        return "\n".join(out)
    out.append("[ipv6-pool]")
    if g.get("delegate"): out.append(f"delegate={g['delegate']}")
    if g.get("prefix"): out.append(g["prefix"])
    out.append("")
    out.append("[ipv6-dhcp]")
    out.append("verbose=1")
    if g.get("dns"): out.append(f"dns={g['dns']}")
    if g.get("domain"): out.append(f"domain={g['domain']}")
    out.append("")
    out.append("[ipv6-nd]")
    out.append("verbose=1")
    if g.get("ra_interval"): out.append(f"ra-interval={g['ra_interval']}")
    out.append("")
    return "\n".join(out)


def generate_gre(config: Dict[str, Dict[str, str]]) -> str:
    """Generate GRE tunnel config — ip tunnel commands for Linux GRE."""
    g = config.get("vpn.d.gre", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# GRE tunnel disabled")
        return "\n".join(out)
    local = g.get("local", "192.168.0.203")
    remote = g.get("remote", "192.168.0.201")
    tunnel_ip = g.get("tunnel_ip", "10.99.0.1/30")
    mtu = g.get("mtu", "1400")
    out.append(f"ip tunnel add gre0 mode gre remote {remote} local {local} ttl 255")
    out.append(f"ip link set gre0 up mtu {mtu}")
    out.append(f"ip addr add {tunnel_ip} dev gre0")
    if g.get("routes"): out.append(f"# ip route add {g['routes']} dev gre0")
    out.append("")
    return "\n".join(out)


def generate_ipip(config: Dict[str, Dict[str, str]]) -> str:
    """Generate IPIP (IP-in-IP) tunnel config — Linux ip tunnel for RouterOS-compatible IPIP."""
    g = config.get("vpn.d.ipip", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# IPIP tunnel disabled")
        return "\n".join(out)
    local = g.get("local", "192.168.0.203")
    remote = g.get("remote", "192.168.0.201")
    tunnel_ip = g.get("tunnel_ip", "10.98.0.1/30")
    mtu = g.get("mtu", "1480")
    out.append(f"ip tunnel add ipip0 mode ipip remote {remote} local {local} ttl 255")
    out.append(f"ip link set ipip0 up mtu {mtu}")
    out.append(f"ip addr add {tunnel_ip} dev ipip0")
    if g.get("routes"): out.append(f"# ip route add {g['routes']} dev ipip0")
    out.append("")
    return "\n".join(out)


def generate_eoip(config: Dict[str, Dict[str, str]]) -> str:
    """Generate EoIP (Ethernet over IP) config — RouterOS-compatible GRE L2 tunnel."""
    g = config.get("vpn.d.eoip", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# EoIP tunnel disabled")
        return "\n".join(out)
    local = g.get("local", "192.168.0.203")
    remote = g.get("remote", "192.168.0.201")
    tid = g.get("tunnel_id", "0")
    mtu = g.get("mtu", "1400")
    ka = g.get("keepalive", "0")
    out.append(f"ip tunnel add eoip{tid} mode gre remote {remote} local {local} ttl 255 key {tid}")
    out.append(f"ip link set eoip{tid} up mtu {mtu}")
    if g.get("mac"): out.append(f"ip link set eoip{tid} address {g['mac']}")
    if g.get("bridge"): out.append(f"ip link set eoip{tid} master {g['bridge']}")
    if ka != "0": out.append(f"ip tunnel change eoip{tid} mode gre key {tid} csum ikey {tid} okey {tid} || true")
    out.append("")
    return "\n".join(out)


def generate_vxlan(config: Dict[str, Dict[str, str]]) -> str:
    """Generate VXLAN tunnel config — L2 overlay over UDP (data center standard)."""
    g = config.get("vpn.d.vxlan", {})
    out = ["# Generated by rnas-config — do not edit", ""]
    if g.get("enabled") != "yes":
        out.append("# VXLAN tunnel disabled")
        return "\n".join(out)
    vni = g.get("vni", "100")
    local = g.get("local", "192.168.0.203")
    remote = g.get("remote", "192.168.0.202")
    dstport = g.get("dstport", "4789")
    mtu = g.get("mtu", "1450")
    out.append(f"ip link add vxlan{vni} type vxlan id {vni} remote {remote} local {local} dstport {dstport}")
    out.append(f"ip link set vxlan{vni} up mtu {mtu}")
    if g.get("learning", "yes") == "no": out.append(f"ip link set vxlan{vni} type vxlan nolearning")
    if g.get("bridge"): out.append(f"ip link set vxlan{vni} master {g['bridge']}")
    out.append("")
    return "\n".join(out)


def find_config_file(root: Path, section_name: str) -> Optional[Path]:
    """Find which .conf file contains a given config section."""
    for conf_file in sorted(root.rglob("*.conf")):
        text = conf_file.read_text()
        # Check both [section] and [section "name"]
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

    # Find section header line
    header_pattern = rf'^\[{re.escape(base)}(\s+"{re.escape(name_part)}")?\]'
    header_idx = -1
    for i, line in enumerate(lines):
        if re.match(header_pattern, line.strip()):
            header_idx = i
            break
    if header_idx < 0:
        return False

    # Replace or append key=value pairs within the section
    existing_keys = set()
    insert_idx = header_idx + 1
    while insert_idx < len(lines):
        stripped = lines[insert_idx].strip()
        if stripped.startswith("[") and not stripped.startswith("#"):
            break  # Next section starts
        m = re.match(r'^(\w[\w_]*)\s*=\s*', stripped)
        if m:
            key = m.group(1)
            if key in values:
                lines[insert_idx] = f"{key} = {values[key]}\n"
                existing_keys.add(key)
        insert_idx += 1

    # Append new keys not found in existing lines
    for key, val in values.items():
        if key not in existing_keys:
            new_line = f"{key} = {val}\n"
            # Insert before next section or at end
            insert_point = header_idx + 1
            while insert_point < len(lines):
                s = lines[insert_point].strip()
                if s.startswith("[") and not s.startswith("#"):
                    break
                insert_point += 1
            lines.insert(insert_point, new_line)

    conf_file.write_text("".join(lines))
    return True


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RNAS Configuration Engine")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Config root directory (default: {DEFAULT_ROOT})")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("show", help="Show parsed config")
    gen = sub.add_parser("generate", help="Generate native service config")
    gen.add_argument("service", choices=["accel-ppp", "dnsmasq", "firewall", "snmp", "qos", "ipsec", "wireguard", "openvpn", "hotspot", "ha", "dhcp-relay", "dot1x", "mac-auth", "ipv6", "vlan", "gre", "ipip", "eoip", "vxlan"], help="Service to generate config for")
    gen.add_argument("--output", "-o", help="Output file (default: stdout)")

    sub.add_parser("validate", help="Validate config tree")
    snap = sub.add_parser("snapshot", help="Manage config snapshots")
    snap.add_argument("action", choices=["create", "list", "restore"], help="Snapshot action")
    snap.add_argument("--name", help="Snapshot name (for create/restore)")

    sc = sub.add_parser("scenario", help="Manage deployment scenarios")
    sc.add_argument("action", choices=["list", "apply"], help="Scenario action")
    sc.add_argument("name", nargs="?", help="Scenario name (for apply)")

    app = sub.add_parser("apply", help="Generate config and restart service")
    app.add_argument("service", choices=["accel-ppp", "dnsmasq", "firewall", "snmp", "qos", "ipsec", "wireguard", "openvpn", "hotspot", "ha", "dhcp-relay"], help="Service to apply")

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
        elif args.service == "qos":
            result = generate_qos(config)
        elif args.service == "ipsec":
            result = generate_ipsec(config)
        elif args.service == "wireguard":
            result = generate_wireguard(config)
        elif args.service == "openvpn":
            result = generate_openvpn(config)
        elif args.service == "hotspot":
            result = generate_hotspot(config)
        elif args.service == "ha":
            result = generate_ha(config)
        elif args.service == "dhcp-relay":
            result = generate_dhcp_relay(config)
        elif args.service == "dot1x":
            result = generate_dot1x(config)
        elif args.service == "mac-auth":
            result = generate_mac_auth(config)
        elif args.service == "ipv6":
            result = generate_ipv6(config)
        elif args.service == "vlan":
            result = generate_vlan(config)
        elif args.service == "gre":
            result = generate_gre(config)
        elif args.service == "ipip":
            result = generate_ipip(config)
        elif args.service == "eoip":
            result = generate_eoip(config)
        elif args.service == "vxlan":
            result = generate_vxlan(config)
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
            import json
            overrides = json.loads(sc_file.read_text())
            for key, val in overrides.get("config", {}).items():
                sec, opt = key.split(".", 1)
                conf_path = Path(args.root)
                for p in sec.split("."):
                    conf_path = conf_path / p
                if not conf_path.exists():
                    conf_path.parent.mkdir(parents=True, exist_ok=True)
                    conf_path.touch()
                # Read existing, update key
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
        gen_map = {"accel-ppp": generate_accel_ppp, "dnsmasq": generate_dnsmasq,
                   "firewall": generate_firewall, "snmp": generate_snmp,
                   "qos": generate_qos, "ipsec": generate_ipsec,
                   "wireguard": generate_wireguard, "openvpn": generate_openvpn,
                   "hotspot": generate_hotspot, "ha": generate_ha,
                   "dhcp-relay": generate_dhcp_relay}
        if svc in gen_map:
            out_dir = Path("/var/run/rnas")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{svc}.conf"
            result = gen_map[svc](config)
            out_file.write_text(result)
            print(f"Generated {out_file}")
            import subprocess
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
