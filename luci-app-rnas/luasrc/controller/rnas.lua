module("luci.controller.rnas", package.seeall)

require("uci")
require("luci.util")
require("luci.sys")

local cached_uci = nil
local function get_uci()
    if not cached_uci then
        cached_uci = uci.cursor()
    end
    return cached_uci
end

function index()
    entry({"admin", "network", "rnas"}, alias("admin", "network", "rnas", "overview"), _("RADIUS NAS"))
    entry({"admin", "network", "rnas", "overview"}, cbi("rnas/overview"), _("Overview"), 1)
    entry({"admin", "network", "rnas", "radius"}, cbi("rnas/radius"), _("RADIUS Settings"), 2)
    entry({"admin", "network", "rnas", "protocol"}, cbi("rnas/protocol"), _("Protocol Config"), 3)
    entry({"admin", "network", "rnas", "ip_pool"}, cbi("rnas/ip_pool"), _("IP Pool"), 4)
    entry({"admin", "network", "rnas", "sessions"}, cbi("rnas/sessions"), _("Sessions"), 5)
    entry({"admin", "network", "rnas", "coa"}, cbi("rnas/coa"), _("CoA Control"), 6)
    entry({"admin", "network", "rnas", "status"}, cbi("rnas/status"), _("Status"), 7)

    entry({"admin", "network", "rnas", "sessions", "terminate"}, call("action_terminate_session"))
    entry({"admin", "network", "rnas", "coa", "disconnect"}, call("action_coa_disconnect"))
    entry({"admin", "network", "rnas", "coa", "timeout"}, call("action_coa_timeout"))
    entry({"admin", "network", "rnas", "status", "data"}, call("get_status_data"))
end

function action_terminate_session()
    local sid = luci.http.formvalue("sid")
    if sid then
        luci.sys.exec("accel-cmd session terminate " .. sid)
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/sessions"))
    end
end

function action_coa_disconnect()
    local username = luci.http.formvalue("username")
    if username then
        local uci = get_uci()
        local secret = uci:get("rnas", "radius", "secret") or "testing123"
        local server = uci:get("rnas", "radius", "auth_server") or "127.0.0.1"
        luci.sys.exec("echo 'User-Name=" .. username .. "' | radclient " .. server .. ":3799 disconnect " .. secret)
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/coa"))
    end
end

function action_coa_timeout()
    local username = luci.http.formvalue("username")
    local timeout = luci.http.formvalue("timeout") or "3600"
    if username then
        local uci = get_uci()
        local secret = uci:get("rnas", "radius", "secret") or "testing123"
        local server = uci:get("rnas", "radius", "auth_server") or "127.0.0.1"
        luci.sys.exec("echo -e 'User-Name=" .. username .. "\\nSession-Timeout=" .. timeout .. "' | radclient " .. server .. ":3799 coa " .. secret)
        luci.http.redirect(luci.dispatcher.build_url("admin/network/rnas/coa"))
    end
end

function get_status_data()
    local uci = get_uci()
    local protocol = uci:get("rnas", "config", "protocol") or "pppoe"
    local sessions = {}
    
    luci.sys.exec("accel-cmd show sessions > /tmp/rnas_sessions.txt 2>/dev/null")
    local f = io.open("/tmp/rnas_sessions.txt", "r")
    if f then
        for line in f:lines() do
            table.insert(sessions, line)
        end
        f:close()
    end

    luci.http.prepare_json()
    luci.http.write_json({
        protocol = protocol,
        sessions = sessions,
        uptime = luci.sys.exec("cat /proc/uptime | cut -d' ' -f1"),
        memory = luci.sys.exec("free | grep Mem | awk '{print $3/$2 * 100}'"),
        cpu = "0"
    })
end
