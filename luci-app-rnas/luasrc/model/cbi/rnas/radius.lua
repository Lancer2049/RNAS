-- RNAS RADIUS Configuration
-- Maps directly to /etc/config/rnas sections: radius, coa, dns

local map = Map("rnas", translate("RADIUS Server Configuration"),
    translate("Configure connection to RADIUS server for authentication, accounting, and CoA."))

-- ===== RADIUS section (named: radius) =====
local rs = map:section(NamedSection, "radius", "radius", translate("RADIUS Server"))

o = rs:option(Value, "auth_server", translate("RADIUS Server IP"))
o.datatype = "ipaddr"
o.placeholder = "192.168.1.1"
o.rmempty = false

o = rs:option(Value, "secret", translate("RADIUS Secret"))
o.datatype = "string"
o.password = true
o.rmempty = false

o = rs:option(Value, "auth_port", translate("Authentication Port"))
o.datatype = "port"
o.default = "1812"

o = rs:option(Value, "acct_port", translate("Accounting Port"))
o.datatype = "port"
o.default = "1813"

o = rs:option(Value, "timeout", translate("Timeout (seconds)"))
o.datatype = "uinteger"
o.default = "30"

o = rs:option(Value, "retries", translate("Retry Count"))
o.datatype = "uinteger"
o.default = "3"

o = rs:option(Value, "interim_interval", translate("Interim Interval (seconds)"))
o.datatype = "uinteger"
o.default = "300"
o:description(translate("Interval for periodic Accounting-Update messages (0 to disable)"))

o = rs:option(Value, "interim_jitter", translate("Interim Jitter (seconds)"))
o.datatype = "uinteger"
o.default = "100"

o = rs:option(Value, "nas_identifier", translate("NAS Identifier"))
o.placeholder = "RNAS"

o = rs:option(Value, "nas_ip_address", translate("NAS IP Address"))
o.datatype = "ipaddr"

o = rs:option(Flag, "message_authenticator", translate("Require Message-Authenticator"))

o = rs:option(Flag, "acct_on", translate("Send Accounting-On at startup"))
o.default = o.disabled

-- ===== CoA section (named: coa) =====
local cs = map:section(NamedSection, "coa", "coa", translate("CoA (Dynamic Authorization)"))

o = cs:option(Flag, "enabled", translate("Enable CoA"))
o.default = o.enabled
o.rmempty = false

o = cs:option(Value, "port", translate("CoA Port"))
o.datatype = "port"
o.default = "3799"
o:depends("enabled", "1")

o = cs:option(Value, "secret", translate("CoA Secret"))
o.password = true
o.placeholder = translate("Same as RADIUS secret")
o:depends("enabled", "1")

-- ===== DNS section (named: dns) =====
local ds = map:section(NamedSection, "dns", "dns", translate("DNS Servers"))

o = ds:option(Value, "dns1", translate("Primary DNS"))
o.datatype = "ipaddr"
o.placeholder = "8.8.8.8"

o = ds:option(Value, "dns2", translate("Secondary DNS"))
o.datatype = "ipaddr"
o.placeholder = "8.8.4.4"

return map
