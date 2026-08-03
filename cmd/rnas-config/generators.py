# ── Accel-PPP generator ─────────────────────────────────────────────────────

from typing import Dict


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
    mac_auth = get_section("access.d.mac_auth")
    w("[modules]")
    mod_list = ["pppoe", "ipoe", "l2tp", "pptp", "sstp", "auth_pap", "auth_chap_md5",
                "auth_mschap_v1", "auth_mschap_v2", "radius", "ippool", "connlimit", "pppd_compat", "log_file", "vlan-mon",
                "ipv6_dhcp", "ipv6_nd", "ipv6pool"]
    for m in mod_list:
        if modules.get(m, "no") == "yes" or core.get(m, "no") == "yes":
            w(m)
    if mac_auth.get("enabled") == "yes" and modules.get("ipoe", "no") != "yes":
        w("ipoe")
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
    elif ppp.get("ipv6") == "allow": w("ipv6=allow")
    if ppp.get("unit_cache") == "yes": w("unit-cache=1")
    w()

    # IPv6 dual-stack (delegated prefix pool + DHCPv6 + SLAAC)
    ipv6 = get_section("network.d.ipv6")
    if ipv6.get("enabled") == "yes":
        w("[ipv6-pool]")
        if ipv6.get("delegate"): w(f"delegate={ipv6['delegate']}")
        if ipv6.get("prefix"): w(ipv6["prefix"])
        w()
        w("[ipv6-dhcp]")
        w("verbose=1")
        if ipv6.get("dns"): w(f"dns={ipv6['dns']}")
        if ipv6.get("domain"): w(f"domain={ipv6['domain']}")
        w()
        w("[ipv6-nd]")
        w("verbose=1")
        if ipv6.get("ra_interval"): w(f"ra-interval={ipv6['ra_interval']}")
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
    mac_auth = get_section("access.d.mac_auth")
    for proto in [("pppoe", "pppoe"), ("pptp", "pptp"), ("l2tp", "l2tp"), ("sstp", "sstp"), ("ipoe", "ipoe")]:
        pconf = get_section(f"access.d.{proto[1]}")
        # MAC-Auth bypass (IPTV/IoT): IPoE in L2 mode with client MAC as username
        if proto[0] == "ipoe" and mac_auth.get("enabled") == "yes":
            w("[ipoe]")
            w("verbose=1")
            iface = mac_auth.get("interface") or pconf.get("interface") or "ens33"
            w(f"interface={iface}")
            w("mode=L2")
            w("start=dhcpv4")
            if mac_auth.get("username_format"):
                w(f"username={mac_auth['username_format']}")
            if mac_auth.get("nas_identifier"):
                w(f"nas-identifier={mac_auth['nas_identifier']}")
            if mac_auth.get("ip_pool"):
                w(f"ip-pool={mac_auth['ip_pool']}")
            if mac_auth.get("vlan"):
                w(f"vlan={mac_auth['vlan']}")
            if pconf.get("speed_limit"):
                w(f"speed-limit={pconf['speed_limit']}")
            w()
            if pconf.get("option60"):
                w("[dhcpv4]")
                w(f"vci={pconf['option60']}")
                w()
            continue
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
        if pconf.get("speed_limit"): w(f"speed-limit={pconf['speed_limit']}")
        if proto[0] == "l2tp": w("dictionary=/usr/share/accel-ppp/l2tp/dictionary")
        w()
        if proto[0] == "ipoe" and pconf.get("option60"):
            w("[dhcpv4]")
            w(f"vci={pconf['option60']}")
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
    # Bind only to the listed interface — otherwise dnsmasq takes the wildcard
    # 0.0.0.0:67/53 socket and collides with other DHCP/DNS listeners
    # (e.g. hostapd wired 802.1X on a dedicated veth pair).
    out.append("bind-interfaces")

    start = dhcp.get("start", "100")
    limit = dhcp.get("limit", "100")
    ip = iface.get("ipaddr", "192.168.100.1")
    netmask = iface.get("netmask", "255.255.255.0")
    lease = dhcp.get("leasetime", "12h")

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
    out.append("[relay]")
    out.append("enabled=yes")
    out.append(f"upstream={upstream}:67")
    out.append(f"giaddr={giaddr}")
    out.append(f"interface={iface}")
    if relay.get("option82") == "yes":
        circuit = relay.get("circuit_id", "rnas-port1")
        remote = relay.get("remote_id", "rnas")
        out.append("option82=yes")
        out.append(f"circuit_id={circuit}")
        out.append(f"remote_id={remote}")
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

    out.append("table inet rnas {")
    out.append("    chain input {")
    out.append("        type filter hook input priority 0; policy drop;")
    out.append("        iif lo accept")
    out.append("        ct state established,related accept")
    out.append("        tcp dport { 22, 80, 443, 8099, 9099 } accept")
    for rname, rv in rules.items():
        if rv.get("target") != "ACCEPT":
            continue
        proto = rv.get("proto")
        ports = rv.get("dest_port", "").replace(" ", "")
        if proto in ("tcp", "udp") and ports:
            out.append(f"        {proto} dport {{ {ports} }} accept")
    out.append("    }")
    out.append("")
    out.append("    chain forward {")
    out.append("        type filter hook forward priority 0; policy drop;")
    out.append(f"        ip saddr {A_NET} accept")
    mcast = config.get("network.d.multicast", {})
    if mcast.get("enabled") == "yes":
        mnet = mcast.get("multicast_net", "224.0.0.0/4")
        out.append(f"        ip daddr {mnet} accept")
        out.append("        meta l4proto igmp accept")
    out.append("    }")
    out.append("")
    out.append("    chain output {")
    out.append("        type filter hook output priority 0; policy accept;")
    out.append("    }")
    out.append("}")

    cgnat = config.get("network.d.cgnat", {})
    if cgnat.get("enabled") == "yes":
        net = cgnat.get("internal_net", "192.168.100.0/24")
        wan = cgnat.get("wan_interface", "ens33")
        out.append("")
        out.append("table ip nat {")
        out.append("    chain postrouting {")
        out.append("        type nat hook postrouting priority 100;")
        out.append(f"        ip saddr {net} oifname \"{wan}\" masquerade")
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
    out.append("    left=%defaultroute")
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
    iface = g.get("interface", "veth-dot1x")
    out.append("interface=" + iface)
    out.append("driver=wired")
    out.append("ieee8021x=1")
    out.append("eapol_version=2")
    out.append(f"auth_server_addr={g.get('auth_server', '192.168.0.202')}")
    out.append(f"auth_server_port={g.get('auth_port', '1812')}")
    out.append(f"auth_server_shared_secret={g.get('auth_secret', 'testing123')}")
    out.append("eap_server=0")
    out.append(f"nas_identifier={g.get('nas_identifier', 'rnas-dot1x')}")
    eap = g.get("eap_methods", "")
    if eap:
        # hostapd does not restrict EAP methods when relaying to an external
        # RADIUS server; the list is preserved as a comment for documentation
        # and for a future built-in EAP server (eap_server=1) mode.
        out.append(f"# eap_methods={eap}")
    if g.get("ca_cert"): out.append(f"ca_cert={g['ca_cert']}")
    if g.get("server_cert"): out.append(f"server_cert={g['server_cert']}")
    if g.get("private_key"): out.append(f"private_key={g['private_key']}")
    out.append("logger_syslog=-1")
    out.append("logger_stdout=-1")
    out.append("ctrl_interface=/var/run/hostapd")
    out.append("ssid=rnas-dot1x")
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


# ── Generator registry (dict dispatch) ──────────────────────────────────────

GEN_MAP = {
    "accel-ppp": generate_accel_ppp,
    "dnsmasq": generate_dnsmasq,
    "firewall": generate_firewall,
    "snmp": generate_snmp,
    "qos": generate_qos,
    "ipsec": generate_ipsec,
    "wireguard": generate_wireguard,
    "openvpn": generate_openvpn,
    "hotspot": generate_hotspot,
    "ha": generate_ha,
    "dhcp-relay": generate_dhcp_relay,
    "dot1x": generate_dot1x,
    "mac-auth": generate_mac_auth,
    "ipv6": generate_ipv6,
    "vlan": generate_vlan,
    "gre": generate_gre,
    "ipip": generate_ipip,
    "eoip": generate_eoip,
    "vxlan": generate_vxlan,
}
