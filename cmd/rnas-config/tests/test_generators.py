"""Unit tests for RNAS config generators."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generators import (
    generate_accel_ppp, generate_dnsmasq, generate_dhcp_relay,
    generate_firewall, generate_snmp, generate_qos,
    generate_ipsec, generate_wireguard, generate_openvpn,
    generate_dot1x, generate_hotspot, generate_ha,
    generate_vlan, generate_mac_auth, generate_ipv6,
    generate_gre, generate_ipip, generate_eoip, generate_vxlan,
    GEN_MAP,
)
from core import parse_config, interpolate_env


# ── helpers ────────────────────────────────────────────────────────────────

def _cfg(**overrides):
    """Build a minimal config dict with defaults + overrides."""
    base = {
        "access.d.core": {"log_file": "/var/log/accel-ppp.log"},
        "access.d.modules": {"pppoe": "yes", "radius": "yes"},
        "access.d.common": {"sid_source": "host"},
        "access.d.server/primary": {"auth_host": "192.168.0.202", "secret": "testing123"},
        "access.d.ppp": {"mtu": "1492"},
        "access.d.pppoe": {"interface": "ens33"},
        "access.d.pool/default": {"range": "192.168.100.10-192.168.100.200"},
    }
    base.update(overrides)
    return base


# ── parse_config tests ─────────────────────────────────────────────────────

class TestParseConfig:
    def test_simple_section(self):
        result = parse_config("[test]\nkey=val\n")
        assert "test" in result
        assert result["test"]["key"] == "val"

    def test_named_section(self):
        result = parse_config('[test "foo"]\nk=1\n')
        assert "test/foo" in result
        assert result["test/foo"]["k"] == "1"

    def test_env_interpolation(self):
        os.environ["_RNAS_TEST"] = "hello"
        result = parse_config("[test]\nk=${_RNAS_TEST}\n")
        assert result["test"]["k"] == "hello"
        del os.environ["_RNAS_TEST"]

    def test_env_default(self):
        result = parse_config("[test]\nk=${_RNAS_MISSING:-default}\n")
        assert result["test"]["k"] == "default"

    def test_comment_skipped(self):
        result = parse_config("[test]\n# comment\nkey=val\n")
        assert result["test"]["key"] == "val"
        assert len(result["test"]) == 1

    def test_empty_input(self):
        result = parse_config("")
        assert result == {}

    def test_multiple_sections(self):
        result = parse_config("[s1]\na=1\n[s2]\nb=2\n")
        assert "s1" in result and "s2" in result


# ── accel-ppp generator tests ──────────────────────────────────────────────

class TestAccelPppGenerator:
    def test_basic_output_structure(self):
        cfg = _cfg()
        out = generate_accel_ppp(cfg)
        assert out.startswith("[modules]")
        assert "[radius]" in out
        assert "[pppoe]" in out
        assert "[common]" in out
        assert "[ppp]" in out
        assert "[log]" in out
        assert "[cli]" in out

    def test_pppoe_interface(self):
        cfg = _cfg()
        out = generate_accel_ppp(cfg)
        assert "interface=ens33" in out

    def test_radius_server(self):
        cfg = _cfg()
        out = generate_accel_ppp(cfg)
        assert "192.168.0.202" in out
        assert "testing123" in out

    def test_module_selection(self):
        cfg = _cfg(**{"access.d.modules": {"pppoe": "yes", "l2tp": "yes", "radius": "no"}})
        out = generate_accel_ppp(cfg)
        assert "pppoe" in out
        assert "l2tp" in out

    def test_ip_pool(self):
        cfg = _cfg()
        out = generate_accel_ppp(cfg)
        assert "192.168.100.10-192.168.100.200" in out

    def test_dae_enabled(self):
        cfg = _cfg(**{"access.d.dae": {"enabled": "yes", "listen": "0.0.0.0:3799", "secret": "test123"}})
        out = generate_accel_ppp(cfg)
        assert "dae-server" in out
        assert "0.0.0.0:3799" in out

    def test_verbose_control(self):
        cfg = _cfg(**{"access.d.pppoe": {"interface": "ens33", "verbose": "0"}})
        out = generate_accel_ppp(cfg)
        assert "verbose=0" in out

    def test_mtu_setting(self):
        cfg = _cfg(**{"access.d.ppp": {"mtu": "1400"}})
        out = generate_accel_ppp(cfg)
        assert "mtu=1400" in out

    def test_mac_auth_merged_into_ipoe(self):
        cfg = _cfg(**{
            "access.d.mac_auth": {
                "enabled": "yes", "interface": "ens44",
                "username_format": "mac", "nas_identifier": "rnas-mac-auth",
                "ip_pool": "default", "vlan": "100",
            },
        })
        out = generate_accel_ppp(cfg)
        assert "[ipoe]" in out
        assert "interface=ens44" in out
        assert "mode=L2" in out
        assert "start=dhcpv4" in out
        assert "username=mac" in out
        assert "nas-identifier=rnas-mac-auth" in out
        assert "ip-pool=default" in out
        assert "vlan=100" in out

    def test_mac_auth_disabled_keeps_regular_ipoe(self):
        cfg = _cfg(**{
            "access.d.ipoe": {"enabled": "yes", "interface": "ens33"},
            "access.d.mac_auth": {"enabled": "no", "interface": "ens44"},
        })
        out = generate_accel_ppp(cfg)
        assert "[ipoe]" in out
        assert "interface=ens33" in out
        assert "username=mac" not in out

    def test_mac_auth_enabled_without_ipoe_module(self):
        cfg = _cfg(**{
            "access.d.modules": {"pppoe": "yes", "radius": "yes"},
            "access.d.mac_auth": {"enabled": "yes", "interface": "ens44", "username_format": "mac"},
        })
        out = generate_accel_ppp(cfg)
        assert "[ipoe]" in out
        assert "username=mac" in out
        mods = out.split("[modules]")[1].split("[core]")[0]
        assert "ipoe" in mods  # forced module load for mac-auth mode

    def test_mac_auth_defaults(self):
        cfg = _cfg(**{"access.d.mac_auth": {"enabled": "yes"}})
        out = generate_accel_ppp(cfg)
        assert "[ipoe]" in out
        assert "interface=ens33" in out  # falls back to ipoe/ens33 default
        assert "mode=L2" in out


# ── dnsmasq generator tests ────────────────────────────────────────────────

class TestDnsmasqGenerator:
    def test_basic_output(self):
        cfg = {"network.d.dhcp/dhcp lan": {},
               "network.d.dhcp/dhcp_option dns": {},
               "network.d.interface/lan": {}}
        out = generate_dnsmasq(cfg)
        assert out.startswith("# Generated")
        assert "interface=br-lan" in out
        assert "dhcp-range=" in out

    def test_custom_values(self):
        cfg = {"network.d.dhcp/dhcp lan": {"start": "50", "limit": "50", "leasetime": "24h"},
               "network.d.dhcp/dhcp_option dns": {"list": "1.1.1.1"},
               "network.d.interface/lan": {"device": "ens33", "ipaddr": "10.0.0.1", "netmask": "255.255.255.0"}}
        out = generate_dnsmasq(cfg)
        assert "interface=ens33" in out
        assert "10.0.0.50" in out
        assert "10.0.0.99" in out
        assert "1.1.1.1" in out
        assert "24h" in out


# ── firewall generator tests ───────────────────────────────────────────────

class TestFirewallGenerator:
    def test_basic_structure(self):
        out = generate_firewall({})
        assert "table inet rnas" in out
        assert "chain input" in out
        assert "chain forward" in out
        assert "chain output" in out
        assert "policy drop" in out
        assert "192.168.100.0/24" in out  # from A_NET


# ── generator disabled state tests ─────────────────────────────────────────

class TestDisabledGenerators:
    def _test_disabled(self, gen_func, cfg_key):
        out = gen_func({cfg_key: {"enabled": "no"}})
        assert "disabled" in out.lower() or "#" in out

    def test_qos_disabled(self):
        self._test_disabled(generate_qos, "qos.global")

    def test_ipsec_disabled(self):
        self._test_disabled(generate_ipsec, "vpn.d.ipsec")

    def test_wireguard_disabled(self):
        self._test_disabled(generate_wireguard, "vpn.d.wireguard")

    def test_openvpn_disabled(self):
        self._test_disabled(generate_openvpn, "vpn.d.openvpn")

    def test_dot1x_disabled(self):
        self._test_disabled(generate_dot1x, "wireless.d.dot1x")

    def test_hotspot_disabled(self):
        self._test_disabled(generate_hotspot, "hotspot.global")

    def test_ha_disabled(self):
        self._test_disabled(generate_ha, "ha.global")

    def test_vlan_disabled(self):
        self._test_disabled(generate_vlan, "network.d.vlan")

    def test_mac_auth_disabled(self):
        self._test_disabled(generate_mac_auth, "access.d.mac_auth")

    def test_ipv6_disabled(self):
        self._test_disabled(generate_ipv6, "network.d.ipv6")

    def test_gre_disabled(self):
        self._test_disabled(generate_gre, "vpn.d.gre")

    def test_ipip_disabled(self):
        self._test_disabled(generate_ipip, "vpn.d.ipip")

    def test_eoip_disabled(self):
        self._test_disabled(generate_eoip, "vpn.d.eoip")

    def test_vxlan_disabled(self):
        self._test_disabled(generate_vxlan, "vpn.d.vxlan")

    def test_dhcp_relay_disabled(self):
        self._test_disabled(generate_dhcp_relay, "network.d.relay")


# ── GEN_MAP registry tests ─────────────────────────────────────────────────

class TestGenMap:
    def test_all_generators_registered(self):
        expected = [
            "accel-ppp", "dnsmasq", "firewall", "snmp", "qos",
            "ipsec", "wireguard", "openvpn", "hotspot", "ha",
            "dhcp-relay", "dot1x", "mac-auth", "ipv6", "vlan",
            "gre", "ipip", "eoip", "vxlan",
        ]
        for key in expected:
            assert key in GEN_MAP, f"Missing generator: {key}"
        assert len(GEN_MAP) == len(expected)

    def test_all_generators_are_callable(self):
        for key, func in GEN_MAP.items():
            assert callable(func), f"{key} is not callable"

    def test_each_generator_returns_string(self):
        for key, func in GEN_MAP.items():
            result = func({})
            assert isinstance(result, str), f"{key} did not return str"
