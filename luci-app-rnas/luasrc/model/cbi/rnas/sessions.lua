local map, section = Map("rnas", translate("Active Sessions"), translate("View and manage active PPPoE/IPoE sessions."))

s = section

local sessions = {}

local cmd = io.popen("accel-cmd show sessions 2>/dev/null || echo ''")
if cmd then
    local output = cmd:read("*a")
    cmd:close()
    
    for line in output:gmatch("[^\r\n]+") do
        if line:match("^%d") then
            local fields = {}
            for field in line:gmatch("[^%s]+") do
                table.insert(fields, field)
            end
            if #fields >= 5 then
                table.insert(sessions, {
                    sid = fields[1],
                    ifname = fields[2],
                    username = fields[3],
                    ipaddr = fields[4],
                    state = fields[5],
                    uptime = fields[6] or "N/A",
                    rx_bytes = fields[7] or "0",
                    tx_bytes = fields[8] or "0"
                })
            end
        end
    end
end

o = s:Option(DummyValue, "_sessions", translate("Active Sessions"))
o.template = "rnas/sessions_table"
o.value = "dummy"

local fs = require("nixio.fs")
local function format_bytes(bytes)
    local b = tonumber(bytes) or 0
    if b < 1024 then return b .. " B" end
    if b < 1024*1024 then return string.format("%.1f KB", b/1024) end
    if b < 1024*1024*1024 then return string.format("%.1f MB", b/1024/1024) end
    return string.format("%.2f GB", b/1024/1024/1024)
end

s._sessions = sessions
s._format_bytes = format_bytes

function s.render_content(self, section)
    local view = require("luci.view")
    local template = require("luci.template")
    
    luci.http.write('<div class="cbi-map">')
    luci.http.write('<fieldset class="cbi-section">')
    luci.http.write('<legend>' .. translate("Active Sessions") .. '</legend>')
    
    if #sessions == 0 then
        luci.http.write('<p>' .. translate("No active sessions") .. '</p>')
    else
        luci.http.write('<table class="cbi-section-table">')
        luci.http.write('<tr>')
        luci.http.write('<th>' .. translate("Session ID") .. '</th>')
        luci.http.write('<th>' .. translate("Interface") .. '</th>')
        luci.http.write('<th>' .. translate("Username") .. '</th>')
        luci.http.write('<th>' .. translate("IP Address") .. '</th>')
        luci.http.write('<th>' .. translate("State") .. '</th>')
        luci.http.write('<th>' .. translate("Uptime") .. '</th>')
        luci.http.write('<th>' .. translate("RX") .. '</th>')
        luci.http.write('<th>' .. translate("TX") .. '</th>')
        luci.http.write('<th>' .. translate("Actions") .. '</th>')
        luci.http.write('</tr>')
        
        for _, sess in ipairs(sessions) do
            luci.http.write('<tr>')
            luci.http.write('<td>' .. sess.sid .. '</td>')
            luci.http.write('<td>' .. sess.ifname .. '</td>')
            luci.http.write('<td>' .. sess.username .. '</td>')
            luci.http.write('<td>' .. sess.ipaddr .. '</td>')
            luci.http.write('<td>' .. sess.state .. '</td>')
            luci.http.write('<td>' .. sess.uptime .. '</td>')
            luci.http.write('<td>' .. format_bytes(sess.rx_bytes) .. '</td>')
            luci.http.write('<td>' .. format_bytes(sess.tx_bytes) .. '</td>')
            luci.http.write('<td>')
            luci.http.write('<a href="' .. luci.dispatcher.build_url("admin/network/rnas/sessions/terminate") .. '?sid=' .. sess.sid .. '" class="cbi-button cbi-button-action important">' .. translate("Terminate") .. '</a>')
            luci.http.write('</td>')
            luci.http.write('</tr>')
        end
        
        luci.http.write('</table>')
    end
    
    luci.http.write('</fieldset>')
    luci.http.write('</div>')
end

return map
