-- RNAS Translation Strings
-- Chinese translations

local api = require("luci.model.cbi.api")
local util = require("luci.util")

return {
	title = "RADIUS NAS",
	overview = "Overview",
	radius_settings = "RADIUS Settings",
	protocol_config = "Protocol Configuration",
	ip_pool = "IP Pool",
	sessions = "Sessions",
	coa_control = "CoA Control",
	status = "Status",
	
	enable = "Enable",
	disable = "Disable",
	enabled = "Enabled",
	disabled = "Disabled",
	
	radius_server = "RADIUS Server",
	radius_secret = "RADIUS Secret",
	auth_port = "Auth Port",
	acct_port = "Acct Port",
	coa_port = "CoA Port",
	timeout = "Timeout",
	retries = "Retries",
	
	pppoe = "PPPoE",
	ipoe = "IPoE",
	l2tp = "L2TP",
	pptp = "PPTP",
	sstp = "SSTP",
	
	active_sessions = "Active Sessions",
	no_active_sessions = "No active sessions",
	terminate = "Terminate",
	
	username = "Username",
	ip_address = "IP Address",
	uptime = "Uptime",
	rx_bytes = "RX",
	tx_bytes = "TX",
	
	disconnect_user = "Disconnect User",
	set_timeout = "Set Session Timeout",
	set_bandwidth = "Set Bandwidth Limits",
	
	save = "Save",
	reset = "Reset",
	apply = "Apply",
	revert = "Revert",
	
	settings_saved = "Settings saved successfully",
	error_occurred = "An error occurred",
	
	protocol_type = "Protocol Type",
	interface = "Interface",
	thread_count = "Thread Count",
	
	gateway_pool_address = "Gateway Pool Address",
	ip_pools = "IP Pools",
	dns_servers = "DNS Servers",
	
	system_overview = "System Overview",
	service_status = "Service Status",
	system_uptime = "System Uptime",
	memory_usage = "Memory Usage",
	load_average = "Load Average",
	
	view_logs = "View Logs",
	refresh = "Refresh",
}
