local map, section = Map("rnas", translate("RADIUS Server Configuration"), translate("Configure connection to RADIUS server for authentication and accounting."))

s = section

o = s:Option(Value, "server", translate("RADIUS Server IP"))
o.datatype = "ipaddr"
o.placeholder = "192.168.1.1"
o.rmempty = false

o = s:Option(Value, "secret", translate("RADIUS Secret"))
o.datatype = "string"
o.password = true
o.rmempty = false

o = s:Option(Value, "auth_port", translate("Authentication Port"))
o.datatype = "port"
o.default = "1812"

o = s:Option(Value, "acct_port", translate("Accounting Port"))
o.datatype = "port"
o.default = "1813"

o = s:Option(Value, "coa_port", translate("CoA Port"))
o.datatype = "port"
o.default = "3799"

o = s:Option(Value, "timeout", translate("Timeout (seconds)"))
o.datatype = "uinteger"
o.default = "30"

o = s:Option(Value, "retries", translate("Retry Count"))
o.datatype = "uinteger"
o.default = "3"

o = s:Option(Flag, "use_radius", translate("Enable RADIUS Authentication"))
o.default = o.enabled

o = s:Option(Flag, "use_accounting", translate("Enable RADIUS Accounting"))
o.default = o.enabled

o = s:Option(Value, "interim_interval", translate("Interim Interval (seconds)"))
o.datatype = "uinteger"
o.default = "300"
o:depends("use_accounting", "1")

return map
