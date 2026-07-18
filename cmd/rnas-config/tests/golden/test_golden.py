"""Golden tests — fixture INI → expected output → diff."""

from pathlib import Path


def test_accel_ppp_generator():
    from generators import generate_accel_ppp
    from core import parse_config

    input_txt = """
[access.d.core]
pppoe=yes
log_file=/var/log/accel-ppp/accel-ppp.log
thread_count=4

[access.d.server/primary]
auth_host=192.168.0.202
secret=testing123
auth_port=1812
acct_port=1813

[access.d.nas]
identifier=RNAS-NAS
ip_address=192.168.0.203
gw_ip_address=192.168.100.1
"""
    tree = parse_config(input_txt)
    output = generate_accel_ppp(tree)

    assert "[radius]" in output
    assert "auth-port=1812" in output  # inside server= string
    assert "server=" in output


def test_dnsmasq_generator():
    from generators import generate_dnsmasq
    from core import parse_config

    input_txt = """
[network.d.dnsmasq]
domain=local
dhcp_range=192.168.100.10,192.168.100.200
lease_time=12h
"""
    tree = parse_config(input_txt)
    output = generate_dnsmasq(tree)

    assert "dhcp-range=" in output
    assert "12h" in output  # lease time propagates


def test_firewall_generator_empty():
    from generators import generate_firewall
    from core import parse_config

    tree = parse_config("[network.d.firewall]\n")
    output = generate_firewall(tree)
    assert "flush ruleset" in output
    assert "table inet" in output


def test_qos_generator_disabled():
    from generators import generate_qos

    config = {"qos": {"enabled": "no"}}
    output = generate_qos(config)
    assert output == "" or "# QoS" in output


def test_gen_map_all_registered():
    from generators import GEN_MAP
    required = [
        "accel-ppp", "dnsmasq", "firewall", "snmp", "qos",
        "ipsec", "wireguard", "openvpn", "hotspot", "ha",
        "dhcp-relay", "dot1x", "mac-auth", "ipv6",
        "vlan", "gre", "ipip", "eoip", "vxlan",
    ]
    for name in required:
        assert name in GEN_MAP, f"Missing generator: {name}"
    assert len(GEN_MAP) == 19, f"Expected 19 generators, got {len(GEN_MAP)}"