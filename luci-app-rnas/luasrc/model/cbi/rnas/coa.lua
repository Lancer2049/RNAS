local map, section = Map("rnas", translate("CoA (Change of Authorization)"), translate("Send CoA requests to modify active sessions."))

s = section
s:tab("disconnect", translate("Disconnect User"))
s:tab("timeout", translate("Set Session Timeout"))
s:tab("bandwidth", translate("Set Bandwidth Limits"))
s:tab("log", translate("CoA Log"))

o = s:taboption("disconnect", Value, "disconnect_username", translate("Username"))
o.datatype = "string"
o.placeholder = "Enter username to disconnect"

o = s:taboption("disconnect", Button, "_disconnect", translate("Send Disconnect"))
o.inputstyle = "remove"
o:depends("disconnect_username", "")

function o.write(self, section)
    local uci = require("uci").cursor()
    local username = map:formvalue("cbid.rnas.disconnect_username")
    local secret = uci:get("rnas", "radius", "secret") or "testing123"
    local server = uci:get("rnas", "radius", "auth_server") or "127.0.0.1"
    local coa_port = uci:get("rnas", "coa", "port") or "3799"
    
    if username and username ~= "" then
        local cmd = string.format('echo "User-Name=%s" | radclient %s:%s disconnect %s 2>&1', 
            username, server, coa_port, secret)
        local handle = io.popen(cmd)
        local result = handle:read("*a")
        handle:close()
        
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/coa") .. "?tab=log&result=disconnect:" .. username)
    end
end

o = s:taboption("timeout", Value, "timeout_username", translate("Username"))
o.datatype = "string"

o = s:taboption("timeout", Value, "timeout_seconds", translate("Session Timeout (seconds)"))
o.datatype = "uinteger"
o.placeholder = "3600"
o.default = "3600"

o = s:taboption("timeout", Button, "_set_timeout", translate("Set Timeout"))
o.inputstyle = "apply"

function o.write(self, section)
    local uci = require("uci").cursor()
    local username = map:formvalue("cbid.rnas.timeout_username")
    local timeout = map:formvalue("cbid.rnas.timeout_seconds") or "3600"
    local secret = uci:get("rnas", "radius", "secret") or "testing123"
    local server = uci:get("rnas", "radius", "auth_server") or "127.0.0.1"
    local coa_port = uci:get("rnas", "coa", "port") or "3799"
    
    if username and username ~= "" then
        local cmd = string.format('echo -e "User-Name=%s\\nSession-Timeout=%s" | radclient %s:%s coa %s 2>&1',
            username, timeout, server, coa_port, secret)
        local handle = io.popen(cmd)
        local result = handle:read("*a")
        handle:close()
        
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/coa") .. "?tab=log&result=timeout:" .. username .. ":" .. timeout)
    end
end

o = s:taboption("bandwidth", Value, "bw_username", translate("Username"))
o.datatype = "string"

o = s:taboption("bandwidth", Value, "bw_downstream", translate("Downstream (kbps)"))
o.datatype = "uinteger"
o.placeholder = "10240"

o = s:taboption("bandwidth", Value, "bw_upstream", translate("Upstream (kbps)"))
o.datatype = "uinteger"
o.placeholder = "5120"

o = s:taboption("bandwidth", Button, "_set_bandwidth", translate("Set Bandwidth"))
o.inputstyle = "apply"

function o.write(self, section)
    local uci = require("uci").cursor()
    local username = map:formvalue("cbid.rnas.bw_username")
    local downstream = map:formvalue("cbid.rnas.bw_downstream") or "10240"
    local upstream = map:formvalue("cbid.rnas.bw_upstream") or "5120"
    local secret = uci:get("rnas", "radius", "secret") or "testing123"
    local server = uci:get("rnas", "radius", "auth_server") or "127.0.0.1"
    local coa_port = uci:get("rnas", "coa", "port") or "3799"
    
    if username and username ~= "" then
        local cmd = string.format('echo -e "User-Name=%s\\nHRc-Downstream-Rate-Limit=%s\\nHRc-Upstream-Rate-Limit=%s" | radclient %s:%s coa %s 2>&1',
            username, downstream, upstream, server, coa_port, secret)
        local handle = io.popen(cmd)
        local result = handle:read("*a")
        handle:close()
        
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/coa") .. "?tab=log&result=bandwidth:" .. username)
    end
end

o = s:taboption("log", DummyValue, "_log", translate("Recent CoA Operations"))
o.template = "rnas/coa_log"

return map
