local map, section = Map("rnas", translate("IP Address Pool"), translate("Configure IP address pools for clients."))

s = section

o = s:Option(Value, "gw_pool_address", translate("Gateway Pool Address"))
o.datatype = "ipaddr"
o.placeholder = "10.0.0.1"

o = s:Option(DynamicList, "pool", translate("IP Pools"))
o.datatype = "iprange"
o.placeholder = "10.0.0.2-10.0.0.254"

o = s:Option(Value, "gw_network", translate("Gateway Network"))
o.datatype = "ipaddr"
o.placeholder = "10.0.0.0/24"

o = s:Option(Value, "dns1", translate("Primary DNS"))
o.datatype = "ipaddr"

o = s:Option(Value, "dns2", translate("Secondary DNS"))
o.datatype = "ipaddr"

s2 = section(Template, "rnas/ip_pool_help")
s2.render = function(self, section)
    local template = require("luci.template")
    template.render("rnas/ip_pool_help", {})
end

return map
