local map, section = Map("rnas", translate("System Status"), translate("View system status and statistics."))

s = section
s:tab("overview", translate("Overview"))
s:tab("connections", translate("Connections"))
s:tab("logs", translate("Logs"))

o = s:taboption("overview", DummyValue, "_overview", translate("System Overview"))
o.template = "rnas/status_overview"

o = s:taboption("connections", DummyValue, "_connections", translate("Active Connections"))
o.template = "rnas/status_connections"

o = s:taboption("logs", TextValue, "_logs", translate("accel-ppp Logs"))
o.rows = 20
o.readonly = true

function o.cfgvalue(self, section)
    local f = io.popen("logread | grep accel-ppp | tail -n 100 2>/dev/null || echo 'No logs available'")
    if f then
        local content = f:read("*a")
        f:close()
        return content
    end
    return "No logs available"
end

o = s:taboption("logs", Button, "_refresh", translate("Refresh Logs"))
o.inputstyle = "apply"

return map
