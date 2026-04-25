local map, section, fort = Map("rnas", translate("RADIUS NAS Overview"), translate("Overview of RADIUS NAS configuration and status."))

s = section
s.tab("general", translate("General"))
s.tab("status", translate("Status"))

o = s.taboption("general", Flag, "enabled", translate("Enable RADIUS NAS"))
o.default = o.enabled
o.rmempty = false

o = s.taboption("general", ListValue, "protocol", translate("Protocol Type"))
o:value("pppoe", "PPPoE")
o:value("ipoe", "IPoE (DHCP+)")
o:value("l2tp", "L2TP")
o:value("pptp", "PPTP")
o:value("sstp", "SSTP")
o.default = "pppoe"

o = s.taboption("general", Value, "interface", translate("Bridge Interface"))
o.placeholder = "br-lan"
o.datatype = "network"

o = s.taboption("general", Value, "thread_count", translate("Thread Count"))
o.datatype = "uinteger"
o.default = "4"

s2 = section(Template, "rnas/status_general")
s2.render = function(self, section)
    local uci = require("uci").cursor()
    local utl = require("luci.util")
    
    local status = {
        enabled = uci:get("rnas", "global", "enabled") or "0",
        protocol = uci:get("rnas", "config", "protocol") or "pppoe",
        uptime = "N/A",
        sessions = "0",
        total_sessions = "0"
    }

    local f = io.popen("accel-cmd show stats 2>/dev/null | grep -E 'active|sessions' || echo ''")
    if f then
        local output = f:read("*a")
        f:close()
        if output:match("active") then
            status.sessions = output:match("active%s+(%d+)") or "0"
        end
    end

    local uptime_file = io.popen("cat /proc/uptime")
    if uptime_file then
        local uptime = uptime_file:read("*a"):match("^%S+")
        uptime_file:close()
        if uptime then
            local seconds = tonumber(uptime)
            if seconds then
                local days = math.floor(seconds / 86400)
                local hours = math.floor((seconds % 86400) / 3600)
                local mins = math.floor((seconds % 3600) / 60)
                status.uptime = string.format("%dd %dh %dm", days, hours, mins)
            end
        end
    end

    local template = require("luci.template")
    template.render("rnas/status_general", {
        status = status,
        uci = uci
    })
end

return map
