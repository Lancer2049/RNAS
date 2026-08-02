<template>
  <div class="rnas-layout">
    <header class="rnas-topbar">
      <div class="t-left">
        <span class="t-brand">RNAS</span>
        <span class="t-sep">|</span>
        <span class="t-host">{{ hostIP }}</span>
        <span class="t-sep">|</span>
        <span class="t-info">uptime: {{ service.uptime || '--' }}</span>
      </div>
      <div class="t-center">
        <span class="t-sessions">{{ sessions.length }} active</span>
        <span class="t-sep">·</span>
        <span class="t-status" :class="radiusOk ? 'ok' : 'err'">{{ radiusOk ? '● RADIUS up' : '○ RADIUS down' }}</span>
        <span class="t-sep">·</span>
        <span class="t-cpu">CPU {{ service.cpu || '--' }}</span>
        <span class="t-alerts" v-if="alertCount > 0" @click="page='system'" title="Services with issues">
          ⚠ {{ alertCount }}
        </span>
      </div>
      <div class="t-right">
        <span class="t-ver">v3.0</span>
        <span class="t-user" v-if="authUser">{{ authUser }} <a @click="logout" class="t-logout" title="Logout">⎋</a></span>
      </div>
    </header>

    <!-- Login overlay when not authenticated -->
    <div v-if="!isAuth" class="login-overlay">
      <div class="login-card">
        <h2>RNAS</h2>
        <p class="login-sub">RADIUS Network Access Server</p>
        <div class="login-form">
          <input v-model="loginUser" placeholder="Username" @keyup.enter="login" />
          <input v-model="loginPass" type="password" placeholder="Password" @keyup.enter="login" />
          <button @click="login" :disabled="loginBusy">{{ loginBusy ? 'Logging in...' : 'Sign In' }}</button>
        </div>
        <p v-if="loginError" class="login-error">{{ loginError }}</p>
      </div>
    </div>

    <div class="rnas-main">
      <nav class="rnas-sidebar">
        <div class="menu-group">
          <div class="menu-label">Status</div>
          <a :class="{sel:page==='overview'}" @click="page='overview'"><span class="si">◉</span> Overview</a>
          <a :class="{sel:page==='sessions'}" @click="page='sessions'"><span class="si">◉</span> Active Sessions <b v-if="sessions.length">{{ sessions.length }}</b></a>
          <a :class="{sel:page==='network'}" @click="page='network'"><span class="si">◉</span> Interfaces</a>
          <a :class="{sel:page==='proto-monitor'}" @click="page='proto-monitor'"><span class="si">◉</span> RADIUS Monitor</a>
          <a :class="{sel:page==='torch'}" @click="page='torch'"><span class="si">◉</span> Traffic Torch</a>
          <a :class="{sel:page==='log'}" @click="page='log'"><span class="si">◉</span> System Log</a>
          <a :class="{sel:page==='ip'}" @click="page='ip'"><span class="si">◉</span> IP Manager</a>
        </div>
        <div class="menu-group">
          <div class="menu-label">Configuration</div>
          <a :class="{sel:page==='proto-config'}" @click="page='proto-config'"><span class="si">◉</span> Access Protocols</a>
          <a :class="{sel:page==='services'}" @click="page='services'"><span class="si">◉</span> VPN Services</a>
          <a :class="{sel:page==='queues'}" @click="page='queues'"><span class="si">◉</span> Queue (QoS)</a>
          <a :class="{sel:page==='config'}" @click="page='config'"><span class="si">◉</span> Config Editor</a>
        </div>
        <div class="menu-group">
          <div class="menu-label">RADIUS</div>
          <a :class="{sel:page==='radius-editor'}" @click="page='radius-editor'"><span class="si">◉</span> AAA Editor</a>
          <a :class="{sel:page==='dictionary'}" @click="page='dictionary'"><span class="si">◉</span> Dictionary</a>
          <a :class="{sel:page==='tools'}" @click="page='tools'"><span class="si">◉</span> RADIUS Tools</a>
          <a :class="{sel:page==='bw-test'}" @click="page='bw-test'"><span class="si">◉</span> Bandwidth Test</a>
          <a :class="{sel:page==='setup'}" @click="page='setup'"><span class="si">◉</span> Quick Setup</a>
          <a :class="{sel:page==='terminal'}" @click="page='terminal'"><span class="si">◉</span> Terminal</a>
          <a :class="{sel:page==='certs'}" @click="page='certs'"><span class="si">◉</span> Certificates</a>
          <a :class="{sel:page==='aaa-users'}" @click="page='aaa-users'"><span class="si">◉</span> AAA Users</a>
          <a :class="{sel:page==='acct-records'}" @click="page='acct-records'"><span class="si">◉</span> Accounting</a>
          <a :class="{sel:page==='user-groups'}" @click="page='user-groups'"><span class="si">◉</span> User Groups</a>
          <a :class="{sel:page==='nas-clients'}" @click="page='nas-clients'"><span class="si">◉</span> NAS Clients</a>
        </div>
        <div class="menu-group">
          <div class="menu-label">Simulation</div>
          <a :class="{sel:page==='subscriber-sim'}" @click="page='subscriber-sim'"><span class="si">◉</span> Subscriber Sim</a>
          <a :class="{sel:page==='scenario-runner'}" @click="page='scenario-runner'"><span class="si">◉</span> Scenario</a>
          <a :class="{sel:page==='fault-inject'}" @click="page='fault-inject'"><span class="si">◉</span> Fault Inject</a>
        </div>
        <div class="menu-group">
          <div class="menu-label">Network</div>
          <a :class="{sel:page==='routing'}" @click="page='routing'"><span class="si">◉</span> Dynamic Routing</a>
          <a :class="{sel:page==='tunnels'}" @click="page='tunnels'"><span class="si">◉</span> Tunnel Manager</a>
          <a :class="{sel:page==='vlans'}" @click="page='vlans'"><span class="si">◉</span> VLAN per User</a>
          <a :class="{sel:page==='hotspot'}" @click="page='hotspot'"><span class="si">◉</span> Hotspot Portal</a>
          <a :class="{sel:page==='netflow'}" @click="page='netflow'"><span class="si">◉</span> NetFlow / DHCP</a>
        </div>
        <div class="sidebar-foot"><div class="dot ok"></div> v3.0 running</div>
      </nav>

      <main class="rnas-content">
        <div v-if="page==='overview'" class="dash-grid">
          <div class="dash-col-main">
            <StatusCard :service="service" />
            <TrafficMonitor @view-interface="showIface" />
          </div>
          <div class="dash-col-side">
            <QuickActions @nav="page=$event" @refresh="fetchData" />
            <SystemHealth />
            <SystemResources />
            <ActivityFeed />
          </div>
        </div>
        <SessionsTable v-if="page==='sessions'||page==='overview'" :sessions="sessions" :loading="loading" @disconnect="handleDisconnect" @refresh="fetchData" @detail="(s) => { selectedSession = s; page = 'session-detail' }" />
        <SessionDetail v-if="page==='session-detail'" :session="selectedSession" @back="page='sessions'" />
        <InterfaceDetail v-if="page==='iface-detail'" :iface="selectedIface" @back="page='overview'" />
        <NetworkConfig v-if="page==='network'" />
        <ConfigEditor v-if="page==='config'" />
        <ServicesConfig v-if="page==='services'" />
        <ProtocolConfig v-if="page==='proto-config'" />
        <ToolsPage v-if="page==='tools'" />
        <BandwidthTest v-if="page==='bw-test'" />
        <QuickSetup v-if="page==='setup'" />
        <WebTerminal v-if="page==='terminal'" />
        <CertManager v-if="page==='certs'" />
        <RADIUSEditor v-if="page==='radius-editor'" />
        <DictionaryBrowser v-if="page==='dictionary'" />
        <SubscriberSim v-if="page==='subscriber-sim'" />
        <ProtoMonitor v-if="page==='proto-monitor'" />
        <TrafficTorch v-if="page==='torch'" />
        <QueueManager v-if="page==='queues'" />
        <PacketSniffer v-if="page==='sniffer'" />
        <Scheduler v-if="page==='scheduler'" />
        <ScenarioRunner v-if="page==='scenario-runner'" />
        <FaultInject v-if="page==='fault-inject'" />
        <SystemPage v-if="page==='system'" />
        <TestResults v-if="page==='test-results'" />
        <RoutingPage v-if="page==='routing'" />
        <TunnelManager v-if="page==='tunnels'" />
        <VlanManager v-if="page==='vlans'" />
        <HotspotManager v-if="page==='hotspot'" />
        <NetflowDhcp v-if="page==='netflow'" />
        <IPManager v-if="page==='ip'" />
        <SystemLog v-if="page==='log'" />
        <AAAUsers v-if="page==='aaa-users'" />
        <AcctRecords v-if="page==='acct-records'" />
        <UserGroups v-if="page==='user-groups'" />
        <NASClients v-if="page==='nas-clients'" />
      </main>
    </div>
    <div class="toast-container"><div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">{{ t.msg }}</div></div>
    <div v-if="pageLoading" class="page-loader"><div class="loader-bar"></div></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, defineAsyncComponent, provide, h } from 'vue'
// Always-loaded (dashboard core)
import StatusCard from './components/StatusCard.vue'
import QuickActions from './components/QuickActions.vue'
import SystemHealth from './components/SystemHealth.vue'
import SystemResources from './components/SystemResources.vue'
import ActivityFeed from './components/ActivityFeed.vue'
import SessionsTable from './components/SessionsTable.vue'
import TrafficMonitor from './components/TrafficMonitor.vue'

// Shared async component loader: delay before showing loader, retry once on error
function lazy(name, loader) {
  return defineAsyncComponent({
    loader,
    delay: 200,
    timeout: 10000,
    onError(error, retry, fail, attempts) {
      if (attempts < 2) { retry(); return }
      console.error(`Failed to load ${name}:`, error)
      fail()
    },
  })
}
// Lazy-loaded (page components)
const SessionDetail = lazy('SessionDetail', () => import('./components/SessionDetail.vue'))
const NetworkConfig = lazy('NetworkConfig', () => import('./components/NetworkConfig.vue'))
const InterfaceDetail = lazy('InterfaceDetail', () => import('./components/InterfaceDetail.vue'))
const ConfigEditor = lazy('ConfigEditor', () => import('./components/ConfigEditor.vue'))
const ServicesConfig = lazy('ServicesConfig', () => import('./components/ServicesConfig.vue'))
const ProtocolConfig = lazy('ProtocolConfig', () => import('./components/ProtocolConfig.vue'))
const ToolsPage = lazy('ToolsPage', () => import('./components/ToolsPage.vue'))
const RADIUSEditor = lazy('RADIUSEditor', () => import('./components/RADIUSEditor.vue'))
const DictionaryBrowser = lazy('DictionaryBrowser', () => import('./components/DictionaryBrowser.vue'))
const RoutingPage = lazy('RoutingPage', () => import('./components/RoutingPage.vue'))
const TunnelManager = lazy('TunnelManager', () => import('./components/TunnelManager.vue'))
const VlanManager = lazy('VlanManager', () => import('./components/VlanManager.vue'))
const HotspotManager = lazy('HotspotManager', () => import('./components/HotspotManager.vue'))
const NetflowDhcp = lazy('NetflowDhcp', () => import('./components/NetflowDhcp.vue'))
const IPManager = lazy('IPManager', () => import('./components/IPManager.vue'))
const SystemLog = lazy('SystemLog', () => import('./components/SystemLog.vue'))
const SubscriberSim = lazy('SubscriberSim', () => import('./components/SubscriberSim.vue'))
const ProtoMonitor = lazy('ProtoMonitor', () => import('./components/ProtoMonitor.vue'))
const TrafficTorch = lazy('TrafficTorch', () => import('./components/TrafficTorch.vue'))
const QueueManager = lazy('QueueManager', () => import('./components/QueueManager.vue'))
const PacketSniffer = lazy('PacketSniffer', () => import('./components/PacketSniffer.vue'))
const Scheduler = lazy('Scheduler', () => import('./components/Scheduler.vue'))
const ScenarioRunner = lazy('ScenarioRunner', () => import('./components/ScenarioRunner.vue'))
const FaultInject = lazy('FaultInject', () => import('./components/FaultInject.vue'))
const SystemPage = lazy('SystemPage', () => import('./components/SystemPage.vue'))
const TestResults = lazy('TestResults', () => import('./components/TestResults.vue'))
const BandwidthTest = lazy('BandwidthTest', () => import('./components/BandwidthTest.vue'))
const QuickSetup = lazy('QuickSetup', () => import('./components/QuickSetup.vue'))
const WebTerminal = lazy('WebTerminal', () => import('./components/WebTerminal.vue'))
const CertManager = lazy('CertManager', () => import('./components/CertManager.vue'))
const AAAUsers = lazy('AAAUsers', () => import('./components/AAAUsers.vue'))
const AcctRecords = lazy('AcctRecords', () => import('./components/AcctRecords.vue'))
const UserGroups = lazy('UserGroups', () => import('./components/UserGroups.vue'))
const NASClients = lazy('NASClients', () => import('./components/NASClients.vue'))

const page = ref(location.hash ? location.hash.replace('#/','') || 'overview' : 'overview')
const pageLoading = ref(false)
watch(page, n => { window.location.hash = '#/' + n; pageLoading.value = true; setTimeout(() => pageLoading.value = false, 300) })
const alertCount = ref(0)
const hostIP = ref('192.168.0.203')
const service = ref({ uptime: '--', cpu: '--', mem: '--' })
const sessions = ref([])
const selectedSession = ref(null)
const selectedIface = ref('ens33')
function showIface(name) { selectedIface.value = name; page.value = 'iface-detail' }
const loading = ref(true)
const radiusOk = ref(false)
const toasts = ref([])
function addToast(msg, type='info') { const id=Date.now(); toasts.value.push({id,msg,type}); setTimeout(()=>toasts.value=toasts.value.filter(t=>t.id!==id), 3500) }
provide('addToast', addToast)

// ── Auth state ──────────────────────────────────────────────────────────
const isAuth = ref(false)
const authUser = ref('')
const loginUser = ref('')
const loginPass = ref('')
const loginError = ref('')
const loginBusy = ref(false)

function getToken() {
  return localStorage.getItem('rnas_token') || sessionStorage.getItem('rnas_token') || ''
}

function setToken(token) {
  localStorage.setItem('rnas_token', token)
  sessionStorage.setItem('rnas_token', token)
}

// Global fetch wrapper: every component's fetch() to /api/* gets the Bearer
// token automatically (sub-components call fetch directly, not via api()).
const _origFetch = window.fetch
window.fetch = function (input, init) {
  const url = typeof input === 'string' ? input : (input && input.url) || ''
  if (url.includes('/api/') && !url.includes('/auth/token')) {
    const headers = new Headers((init && init.headers) || {})
    const tok = getToken()
    if (tok && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${tok}`)
    return _origFetch(input, { ...(init || {}), headers })
  }
  return _origFetch(input, init)
}

// Wrapper that attaches the Bearer token to every API request and forces
// logout on 401 so the login overlay reappears.
async function api(path, opts = {}) {
  const headers = new Headers(opts.headers || {})
  const tok = getToken()
  if (tok && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${tok}`)
  const res = await fetch(path, { ...opts, headers })
  if (res.status === 401 && !path.includes('/auth/token')) {
    logout()
    throw new Error('Not authenticated')
  }
  return res
}

async function login() {
  if (!loginUser.value || !loginPass.value) { loginError.value = 'Username and password required'; return }
  loginBusy.value = true; loginError.value = ''
  try {
    const res = await fetch('/api/auth/token', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: loginUser.value, password: loginPass.value }),
    })
    const d = await res.json()
    if (!res.ok) { loginError.value = d.detail || 'Invalid credentials'; return }
    setToken(d.access_token)
    isAuth.value = true
    authUser.value = loginUser.value
    loginPass.value = ''
    fetchData(); fetchAlerts(); connectWS()
  } catch (e) {
    loginError.value = 'Network error: ' + (e && e.message ? e.message : e)
  } finally {
    loginBusy.value = false
  }
}

function logout() {
  localStorage.removeItem('rnas_token')
  sessionStorage.removeItem('rnas_token')
  isAuth.value = false
  authUser.value = ''
  if (ws) { ws.close(); ws = null }
}

async function fetchData() {
  loading.value = true
  try { const res = await api('/api/status'); const d = await res.json(); service.value = d.service||{}; sessions.value = d.sessions||[]; radiusOk.value = d.service?.radius_state === 'active' } catch(e){}
  loading.value = false
}
async function fetchAlerts() {
  try { const r = await api('/api/system/health/alerts'); const d = await r.json(); alertCount.value = (d.critical||0) + (d.total||0) } catch {}
}
async function handleDisconnect(sid) { await api(`/api/sessions/${sid}/disconnect`,{method:'POST'}); fetchData() }

let refreshTimer = null, alertTimer = null, ws = null
function connectWS() {
  try {
    const token = getToken()
    ws = new WebSocket(`ws://${location.host}/api/ws?token=${encodeURIComponent(token)}`)
    ws.onmessage = e => {
      try {
        const d = JSON.parse(e.data)
        // Delta push: only changed fields arrive — merge, don't overwrite,
        // so a push without service.radius_state keeps the previous value.
        if (d.service && typeof d.service === 'object') service.value = { ...service.value, ...d.service }
        if (d.sessions && Array.isArray(d.sessions)) sessions.value = d.sessions
        const rs = d.service && d.service.radius_state
        if (rs !== undefined) radiusOk.value = rs === 'active'
      } catch {}
    }
    ws.onclose = () => { ws=null; setTimeout(connectWS,3000) }
    ws.onerror = () => { ws?.close(); ws=null }
  } catch { ws=null }
}
onMounted(()=>{ 
  const tok = getToken()
  if (tok) {
    isAuth.value = true
    authUser.value = 'admin'
    fetchData(); fetchAlerts(); connectWS()
  }
  refreshTimer=setInterval(() => { if (isAuth.value) fetchData() },15000)
  alertTimer=setInterval(() => { if (isAuth.value) fetchAlerts() },30000)
  window.addEventListener('hashchange', () => {
    const h = location.hash.replace('#/','') || 'overview'
    if (h !== page.value) page.value = h
  })
  // Preload common pages after initial load
  setTimeout(() => {
    import('./components/IPManager.vue')
    import('./components/ToolsPage.vue')
    import('./components/SystemLog.vue')
  }, 2000)
})
onUnmounted(()=>{ clearInterval(refreshTimer); clearInterval(alertTimer); ws?.close() })
</script>

<style>
/* ===== RNAS RouterOS-Style Dark Theme v2 ===== */
:root {
  --bg: #0d1117;
  --bg2: #161b22;
  --bg3: #21262d;
  --fg: #e6edf3;
  --fg2: #8b949e;
  --fg3: #484f58;
  --accent: #0abde3;
  --green: #10ac84;
  --red: #ee5253;
  --orange: #ff9f43;
  --border: #30363d;
  --radius: 6px;
  --font: 'Segoe UI', 'Noto Sans SC', system-ui, -apple-system, sans-serif;
  --mono: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: var(--font); background: var(--bg); color: var(--fg); font-size: 13px; line-height: 1.5; -webkit-font-smoothing: antialiased; }
.rnas-layout { display:flex; flex-direction:column; height:100vh; }

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:var(--fg3); }

/* Topbar */
.rnas-topbar { display:flex; align-items:center; height:38px; padding:0 16px; background:var(--bg2); border-bottom:1px solid var(--border); font-size:12px; flex-shrink:0; }
.rnas-topbar .t-left { display:flex; align-items:center; gap:10px; }
.rnas-topbar .t-brand { font-weight:800; color:var(--accent); letter-spacing:2px; font-size:15px; background:rgba(10,189,227,0.08); padding:2px 10px; border-radius:var(--radius); }
.rnas-topbar .t-sep { color:var(--fg3); font-size:10px; }
.rnas-topbar .t-host { color:var(--fg); font-family:var(--mono); font-size:11px; }
.rnas-topbar .t-info { color:var(--fg2); font-size:11px; }
.rnas-topbar .t-center { display:flex; align-items:center; gap:10px; margin:0 auto; }
.rnas-topbar .t-sessions { color:var(--fg); font-weight:600; background:rgba(10,189,227,0.06); padding:2px 8px; border-radius:10px; font-size:11px; }
.rnas-topbar .t-status { font-weight:600; font-size:11px; }
.rnas-topbar .t-status.ok { color:var(--green); }
.rnas-topbar .t-status.err { color:var(--red); }
.rnas-topbar .t-cpu { color:var(--fg2); font-size:11px; }
.rnas-topbar .t-alerts { display:inline-flex; align-items:center; gap:3px; background:rgba(238,82,83,0.12); color:var(--red); padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700; cursor:pointer; }
.rnas-topbar .t-alerts:hover { background:rgba(238,82,83,0.25); }
.rnas-topbar .t-right { display:flex; align-items:center; }
.rnas-topbar .t-ver { color:var(--fg3); font-family:var(--mono); font-size:10px; }

/* Main area */
.rnas-main { display:flex; flex:1; overflow:hidden; }

/* Sidebar */
.rnas-sidebar { width:195px; background:var(--bg2); border-right:1px solid var(--border); overflow-y:auto; flex-shrink:0; font-size:12px; }
.menu-group { padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.03); }
.menu-label { padding:10px 14px 5px; font-size:9px; text-transform:uppercase; color:var(--fg3); letter-spacing:1.5px; font-weight:700; }
.rnas-sidebar a { display:flex; align-items:center; gap:8px; padding:7px 14px 7px 18px; color:var(--fg2); text-decoration:none; cursor:pointer; border-left:2px solid transparent; transition:all .12s; font-size:12px; }
.rnas-sidebar a:hover { background:var(--bg3); color:var(--fg); }
.rnas-sidebar a.sel { background:rgba(10,189,227,0.06); color:var(--accent); border-left-color:var(--accent); font-weight:600; }
.rnas-sidebar a .si { font-size:10px; color:var(--fg3); width:14px; text-align:center; flex-shrink:0; opacity:0.6; }
.rnas-sidebar a.sel .si { color:var(--accent); opacity:1; }
.rnas-sidebar a b { margin-left:auto; background:var(--accent); color:#000; padding:0 7px; border-radius:10px; font-size:9px; font-weight:700; line-height:1.6; }
.sidebar-foot { padding:10px 14px; color:var(--fg3); font-size:10px; display:flex; align-items:center; gap:6px; }
.sidebar-foot .dot { width:6px; height:6px; border-radius:50%; }
.sidebar-foot .dot.ok { background:var(--green); }

/* Toast */
.toast-container { position:fixed; bottom:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:6px; }
.toast { padding:10px 18px; border-radius:var(--radius); font-size:12px; font-weight:600; box-shadow:0 4px 16px rgba(0,0,0,0.4); animation:toast-in .25s; min-width:200px; }
.toast.info { background:var(--accent); color:#000; }
.toast.ok { background:var(--green); color:#000; }
.toast.err { background:var(--red); color:#fff; }
@keyframes toast-in { from{transform:translateY(12px);opacity:0} to{transform:translateY(0);opacity:1} }

/* Content */
.rnas-content { flex:1; overflow-y:auto; padding:20px 24px; background:var(--bg); }
.dash-grid { display:grid; grid-template-columns:1.5fr 1fr; gap:16px; align-items:start; }
.dash-col-main { display:flex; flex-direction:column; gap:14px; }
.dash-col-side { display:flex; flex-direction:column; gap:14px; }

/* Component containers */
.rnas-content h2 { font-size:16px; font-weight:700; color:var(--fg); margin-bottom:10px; letter-spacing:-0.3px; }
.rnas-content .hint, .rnas-content .page-hint { font-size:11px; color:var(--fg2); margin-bottom:14px; }

/* Tables */
table { width:100%; border-collapse:separate; border-spacing:0; background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); font-size:12px; overflow:hidden; }
th { background:var(--bg3); color:var(--fg2); font-weight:600; padding:9px 12px; text-align:left; border-bottom:1px solid var(--border); font-size:10px; text-transform:uppercase; letter-spacing:0.5px; position:sticky; top:0; }
td { padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.03); font-size:12px; }
tbody tr:last-child td { border-bottom:none; }
tbody tr:nth-child(even) { background:rgba(255,255,255,0.015); }
tbody tr:hover { background:rgba(10,189,227,0.03); }
.mono { font-family:var(--mono); }

/* Status tags */
.tag { display:inline-block; padding:2px 10px; border-radius:10px; font-size:10px; font-weight:700; }
.tag.ok { background:rgba(16,172,132,0.12); color:var(--green); }
.tag.err { background:rgba(238,82,83,0.12); color:var(--red); }
.tag.info { background:rgba(10,189,227,0.1); color:var(--accent); }
.tag.warn { background:rgba(255,159,67,0.12); color:var(--orange); }

/* Buttons */
button { font-family:var(--font); cursor:pointer; }
.btn { padding:7px 16px; border:1px solid var(--border); border-radius:var(--radius); background:var(--bg3); color:var(--fg); font-size:12px; font-weight:600; transition:all .15s; }
.btn:hover { background:var(--accent); color:#000; border-color:var(--accent); transform:translateY(-1px); box-shadow:0 2px 8px rgba(10,189,227,0.15); }
.btn:active { transform:translateY(0); }
.btn:disabled { opacity:0.35; cursor:default; transform:none; box-shadow:none; }
.btn-accent { background:var(--accent); color:#000; border-color:var(--accent); }
.btn-danger { background:var(--red); color:#fff; border-color:var(--red); }
.btn-danger:hover { background:#ff6b6b; border-color:#ff6b6b; color:#fff; }

/* Inputs */
input, select, textarea { background:var(--bg); border:1px solid var(--border); color:var(--fg); padding:7px 12px; border-radius:var(--radius); font-size:12px; font-family:var(--font); transition:border-color .15s; }
input:focus, select:focus, textarea:focus { outline:none; border-color:var(--accent); box-shadow:0 0 0 2px rgba(10,189,227,0.1); }

/* Cards */
.card, .section, .tool-section, .hotspot-section, .routing-section, .tunnel-section, .vlan-section, .sim-section { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius); padding:16px; margin-bottom:12px; transition:border-color .15s; }
.card:hover { border-color:rgba(10,189,227,0.15); }

/* Empty state */
.empty, .empty-state { text-align:center; padding:40px; color:var(--fg3); font-size:13px; }
.page-loader { position:fixed; top:0; left:0; right:0; height:2px; z-index:9998; pointer-events:none; }
.loader-bar { height:100%; background:var(--accent); width:30%; animation:loader-slide 1.2s ease-in-out infinite; border-radius:0 2px 2px 0; }
@keyframes loader-slide { 0%{transform:translateX(-100%)} 100%{transform:translateX(400%)} }

/* Login overlay */
.login-overlay { position:fixed; inset:0; z-index:9999; background:var(--bg); display:flex; align-items:center; justify-content:center; }
.login-card { background:var(--bg2); border:1px solid var(--border); border-radius:8px; padding:36px 40px; width:320px; text-align:center; }
.login-card h2 { font-size:24px; color:var(--fg); margin:0 0 4px; font-weight:700; letter-spacing:1px; }
.login-sub { font-size:11px; color:var(--fg3); margin:0 0 24px; }
.login-form { display:flex; flex-direction:column; gap:10px; }
.login-form input { padding:10px 12px; background:var(--bg); border:1px solid var(--border); border-radius:4px; color:var(--fg); font-size:13px; outline:none; font-family:var(--font); }
.login-form input:focus { border-color:var(--accent); }
.login-form button { padding:10px; background:var(--accent); color:#000; border:none; border-radius:4px; font-size:14px; font-weight:600; cursor:pointer; font-family:var(--font); }
.login-form button:disabled { opacity:0.5; }
.login-error { color:var(--red); font-size:12px; margin-top:12px; }
.t-user { margin-left:10px; font-size:11px; color:var(--fg2); }
.t-logout { margin-left:4px; cursor:pointer; color:var(--fg3); text-decoration:none; }
.t-logout:hover { color:var(--red); }
</style>
