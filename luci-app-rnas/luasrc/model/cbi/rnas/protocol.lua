local map, section, fort = Map("rnas", translate("Protocol Configuration"), translate("Configure access protocol settings."))

s = section
s:tab("pppoe", translate("PPPoE"))
s:tab("ipoe", translate("IPoE"))
s:tab("l2tp", translate("L2TP"))
s:tab("pptp", translate("PPTP"))
s:tab("sstp", translate("SSTP"))

o = s:taboption("pppoe", Flag, "pppoe_enabled", translate("Enable PPPoE"))
o.default = o.enabled

o = s:taboption("pppoe", Value, "pppoe_interface", translate("Interface"))
o.placeholder = "br-lan"

o = s:taboption("pppoe", Value, "pppoe_mtu", translate("MTU"))
o.datatype = "uinteger"
o.default = "1492"

o = s:taboption("pppoe", Value, "pppoe_mru", translate("MRU"))
o.datatype = "uinteger"
o.default = "1492"

o = s:taboption("pppoe", Value, "pppoe_service_name", translate("Service Name"))

o = s:taboption("pppoe", Value, "pppoe_ac_name", translate("AC Name"))

o = s:taboption("ipoe", Flag, "ipoe_enabled", translate("Enable IPoE"))
o.default = o.disabled

o = s:taboption("ipoe", Value, "ipoe_interface", translate("Interface"))
o.placeholder = "br-lan"

o = s:taboption("ipoe", ListValue, "ipoe_mode", translate("Mode"))
o:value("L2", "Layer 2")
o:value("L3", "Layer 3")
o.default = "L2"

o = s:taboption("ipoe", Value, "ipoe_username_format", translate("Username Format"))
o:value("mac", "MAC Address")
o:value("dhcp", "DHCP Option")
o.default = "mac"

o = s:taboption("ipoe", Value, "ipoe_lease_time", translate("Lease Time (seconds)"))
o.datatype = "uinteger"
o.default = "600"

o = s:taboption("l2tp", Flag, "l2tp_enabled", translate("Enable L2TP"))
o.default = o.disabled

o = s:taboption("l2tp", Value, "l2tp_listen", translate("Listen Address"))
o.datatype = "ipaddr"
o.placeholder = "0.0.0.0"

o = s:taboption("l2tp", Value, "l2tp_port", translate("Port"))
o.datatype = "port"
o.default = "1701"

o = s:taboption("l2tp", Value, "l2tp_hello_interval", translate("Hello Interval"))
o.datatype = "uinteger"
o.default = "60"

o = s:taboption("pptp", Flag, "pptp_enabled", translate("Enable PPTP"))
o.default = o.disabled

o = s:taboption("pptp", Value, "pptp_listen", translate("Listen Address"))
o.datatype = "ipaddr"
o.placeholder = "0.0.0.0"

o = s:taboption("pptp", Value, "pptp_port", translate("Port"))
o.datatype = "port"
o.default = "1723"

o = s:taboption("pptp", Flag, "pptp_mppe", translate("Enable MPPE Encryption"))
o.default = o.enabled

o = s:taboption("sstp", Flag, "sstp_enabled", translate("Enable SSTP"))
o.default = o.disabled

o = s:taboption("sstp", Value, "sstp_listen", translate("Listen Address"))
o.datatype = "ipaddr"
o.placeholder = "0.0.0.0"

o = s:taboption("sstp", Value, "sstp_port", translate("Port"))
o.datatype = "port"
o.default = "443"

o = s:taboption("sstp", Value, "sstp_cert", translate("SSL Certificate Path"))

o = s:taboption("sstp", Value, "sstp_key", translate("SSL Key Path"))

return map
