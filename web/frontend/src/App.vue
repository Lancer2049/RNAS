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
      </div>
    </header>

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
            <SessionsTable :sessions="sessions" :loading="loading" @disconnect="handleDisconnect" @refresh="fetchData" @detail="(s) => { selectedSession = s; page = 'session-detail' }" />
            <TrafficMonitor @view-interface="showIface" />
          </div>
          <div class="dash-col-side">
            <QuickActions @nav="page=$event" @refresh="fetchData" />
            <SystemHealth />
            <SystemResources />
            <ActivityFeed />
          </div>
        </div>
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
      </main>
    </div>
    <div class="toast-container"><div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">{{ t.msg }}</div></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, defineAsyncComponent, provide } from 'vue'
// Always-loaded (dashboard core)
import StatusCard from './components/StatusCard.vue'
import QuickActions from './components/QuickActions.vue'
import SystemHealth from './components/SystemHealth.vue'
import SystemResources from './components/SystemResources.vue'
import ActivityFeed from './components/ActivityFeed.vue'
import SessionsTable from './components/SessionsTable.vue'
import TrafficMonitor from './components/TrafficMonitor.vue'
// Lazy-loaded (page components)
const SessionDetail = defineAsyncComponent(() => import('./components/SessionDetail.vue'))
const NetworkConfig = defineAsyncComponent(() => import('./components/NetworkConfig.vue'))
const InterfaceDetail = defineAsyncComponent(() => import('./components/InterfaceDetail.vue'))
const ConfigEditor = defineAsyncComponent(() => import('./components/ConfigEditor.vue'))
const ServicesConfig = defineAsyncComponent(() => import('./components/ServicesConfig.vue'))
const ProtocolConfig = defineAsyncComponent(() => import('./components/ProtocolConfig.vue'))
const ToolsPage = defineAsyncComponent(() => import('./components/ToolsPage.vue'))
const RADIUSEditor = defineAsyncComponent(() => import('./components/RADIUSEditor.vue'))
const DictionaryBrowser = defineAsyncComponent(() => import('./components/DictionaryBrowser.vue'))
const RoutingPage = defineAsyncComponent(() => import('./components/RoutingPage.vue'))
const TunnelManager = defineAsyncComponent(() => import('./components/TunnelManager.vue'))
const VlanManager = defineAsyncComponent(() => import('./components/VlanManager.vue'))
const HotspotManager = defineAsyncComponent(() => import('./components/HotspotManager.vue'))
const NetflowDhcp = defineAsyncComponent(() => import('./components/NetflowDhcp.vue'))
const IPManager = defineAsyncComponent(() => import('./components/IPManager.vue'))
const SystemLog = defineAsyncComponent(() => import('./components/SystemLog.vue'))
const SubscriberSim = defineAsyncComponent(() => import('./components/SubscriberSim.vue'))
const ProtoMonitor = defineAsyncComponent(() => import('./components/ProtoMonitor.vue'))
const TrafficTorch = defineAsyncComponent(() => import('./components/TrafficTorch.vue'))
const QueueManager = defineAsyncComponent(() => import('./components/QueueManager.vue'))
const PacketSniffer = defineAsyncComponent(() => import('./components/PacketSniffer.vue'))
const Scheduler = defineAsyncComponent(() => import('./components/Scheduler.vue'))
const ScenarioRunner = defineAsyncComponent(() => import('./components/ScenarioRunner.vue'))
const FaultInject = defineAsyncComponent(() => import('./components/FaultInject.vue'))
const SystemPage = defineAsyncComponent(() => import('./components/SystemPage.vue'))
const TestResults = defineAsyncComponent(() => import('./components/TestResults.vue'))
const BandwidthTest = defineAsyncComponent(() => import('./components/BandwidthTest.vue'))
const QuickSetup = defineAsyncComponent(() => import('./components/QuickSetup.vue'))
const WebTerminal = defineAsyncComponent(() => import('./components/WebTerminal.vue'))
const CertManager = defineAsyncComponent(() => import('./components/CertManager.vue'))

const page = ref(location.hash ? location.hash.replace('#/','') || 'overview' : 'overview')
const alertCount = ref(0)
watch(page, n => window.location.hash = '#/' + n)
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

async function fetchData() {
  loading.value = true
  try { const res = await fetch('/api/status'); const d = await res.json(); service.value = d.service||{}; sessions.value = d.sessions||[]; radiusOk.value = d.service?.radius_state === 'active' } catch(e){}
  loading.value = false
}
async function fetchAlerts() {
  try { const r = await fetch('/api/system/health/alerts'); const d = await r.json(); alertCount.value = (d.critical||0) + (d.total||0) } catch {}
}
async function handleDisconnect(sid) { await fetch(`/api/sessions/${sid}/disconnect`,{method:'POST'}); fetchData() }

let refreshTimer = null, ws = null
function connectWS() {
  try {
    ws = new WebSocket(`ws://${location.host}/api/ws`)
    ws.onmessage = e => { try { const d=JSON.parse(e.data); service.value=d.service||{}; sessions.value=d.sessions||[]; radiusOk.value=d.service?.radius_state==='active' } catch {} }
    ws.onclose = () => { ws=null; setTimeout(connectWS,3000) }
    ws.onerror = () => { ws?.close(); ws=null }
  } catch { ws=null }
}
onMounted(()=>{ 
  fetchData(); fetchAlerts(); refreshTimer=setInterval(fetchData,15000); setInterval(fetchAlerts,30000); connectWS()
  window.addEventListener('hashchange', () => {
    const h = location.hash.replace('#/','') || 'overview'
    if (h !== page.value) page.value = h
  })
})
onUnmounted(()=>{ clearInterval(refreshTimer); ws?.close() })
</script>

<style>
/* ===== RNAS RouterOS-Style Global Theme ===== */
:root {
  --bg: #0f1923;
  --bg2: #1a2733;
  --bg3: #243447;
  --fg: #c8d6e5;
  --fg2: #8395a7;
  --fg3: #576574;
  --accent: #0abde3;
  --green: #10ac84;
  --red: #ee5253;
  --border: #2e4052;
  --font: 'Segoe UI', 'Noto Sans SC', system-ui, sans-serif;
  --mono: 'Cascadia Code', 'Consolas', monospace;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: var(--font); background: var(--bg); color: var(--fg); font-size: 13px; line-height: 1.5; }
.rnas-layout { display:flex; flex-direction:column; height:100vh; }

/* Topbar */
.rnas-topbar { display:flex; align-items:center; height:36px; padding:0 16px; background: var(--bg2); border-bottom:1px solid var(--border); font-size:12px; flex-shrink:0; }
.rnas-topbar .t-left { display:flex; align-items:center; gap:8px; }
.rnas-topbar .t-brand { font-weight:800; color:var(--accent); letter-spacing:2px; font-size:14px; }
.rnas-topbar .t-sep { color:var(--fg3); }
.rnas-topbar .t-host { color:var(--fg); font-family:var(--mono); }
.rnas-topbar .t-info { color:var(--fg2); }
.rnas-topbar .t-center { display:flex; align-items:center; gap:8px; margin:0 auto; }
.rnas-topbar .t-sessions { color:var(--fg); font-weight:600; }
.rnas-topbar .t-status { font-weight:600; }
.rnas-topbar .t-status.ok { color:var(--green); }
.rnas-topbar .t-status.err { color:var(--red); }
.rnas-topbar .t-cpu { color:var(--fg2); }
.rnas-topbar .t-alerts { display:inline-flex; align-items:center; gap:3px; background:rgba(238,82,83,0.15); color:var(--red); padding:1px 8px; border-radius:8px; font-size:10px; font-weight:700; cursor:pointer; }
.rnas-topbar .t-right { display:flex; align-items:center; }
.rnas-topbar .t-ver { color:var(--fg3); font-family:var(--mono); font-size:11px; }

/* Main area */
.rnas-main { display:flex; flex:1; overflow:hidden; }

/* Sidebar */
.rnas-sidebar { width:190px; background:var(--bg2); border-right:1px solid var(--border); overflow-y:auto; flex-shrink:0; font-size:12px; }
.menu-group { padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.menu-label { padding:10px 14px 4px; font-size:9px; text-transform:uppercase; color:var(--fg3); letter-spacing:1.5px; font-weight:700; }
.rnas-sidebar a { display:flex; align-items:center; gap:6px; padding:6px 14px 6px 18px; color:var(--fg2); text-decoration:none; cursor:pointer; border-left:2px solid transparent; transition:0.1s; }
.rnas-sidebar a:hover { background:var(--bg3); color:var(--fg); }
.rnas-sidebar a.sel { background:rgba(10,189,227,0.08); color:var(--accent); border-left-color:var(--accent); font-weight:600; }
.rnas-sidebar a .si { font-size:8px; color:var(--fg3); width:12px; text-align:center; flex-shrink:0; }
.rnas-sidebar a.sel .si { color:var(--accent); }
.rnas-sidebar a b { margin-left:auto; background:var(--accent); color:#000; padding:0 6px; border-radius:8px; font-size:10px; font-weight:700; }
.toast-container { position:fixed; bottom:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:6px; }
.toast { padding:10px 16px; border-radius:4px; font-size:12px; font-weight:600; box-shadow:0 4px 12px rgba(0,0,0,0.3); animation:toast-in .25s; min-width:200px; }
.toast.info { background:var(--accent); color:#000; }
.toast.ok { background:var(--green); color:#000; }
.toast.err { background:var(--red); color:#fff; }
@keyframes toast-in { from{transform:translateY(10px);opacity:0} to{transform:translateY(0);opacity:1} }
.sidebar-foot { padding:10px 14px; color:var(--fg3); font-size:10px; display:flex; align-items:center; gap:6px; }
.sidebar-foot .dot { width:6px; height:6px; border-radius:50%; }
.sidebar-foot .dot.ok { background:var(--green); }

/* Content */
.rnas-content { flex:1; overflow-y:auto; padding:16px 20px; background:var(--bg); }
.dash-grid { display:grid; grid-template-columns:1.5fr 1fr; gap:16px; align-items:start; }
.dash-col-main { display:flex; flex-direction:column; gap:14px; }
.dash-col-side { display:flex; flex-direction:column; gap:14px; }

/* Global component containers */
.rnas-content h2 { font-size:15px; font-weight:600; color:var(--fg); margin-bottom:8px; }
.rnas-content .hint, .rnas-content .page-hint { font-size:11px; color:var(--fg2); margin-bottom:12px; }

/* Tables */
table { width:100%; border-collapse:collapse; background:var(--bg2); border:1px solid var(--border); font-size:12px; }
th { background:var(--bg3); color:var(--fg2); font-weight:600; padding:8px 10px; text-align:left; border-bottom:1px solid var(--border); font-size:10px; text-transform:uppercase; letter-spacing:0.5px; }
td { padding:7px 10px; border-bottom:1px solid rgba(255,255,255,0.03); font-family:var(--mono); font-size:12px; }
tbody tr:hover { background:var(--bg3); }
.mono { font-family:var(--mono); }

/* Status tags */
.tag { display:inline-block; padding:1px 8px; border-radius:3px; font-size:10px; font-weight:700; }
.tag.ok { background:rgba(16,172,132,0.15); color:var(--green); }
.tag.err { background:rgba(238,82,83,0.15); color:var(--red); }
.tag.info { background:rgba(10,189,227,0.12); color:var(--accent); }

/* Buttons */
button { font-family:var(--font); cursor:pointer; }
.btn { padding:6px 14px; border:1px solid var(--border); border-radius:3px; background:var(--bg3); color:var(--fg); font-size:12px; font-weight:600; }
.btn:hover { background:var(--accent); color:#000; border-color:var(--accent); }
.btn:disabled { opacity:0.4; cursor:default; }
.btn-accent { background:var(--accent); color:#000; border-color:var(--accent); }
.btn-danger { background:var(--red); color:#fff; border-color:var(--red); }

/* Inputs */
input, select, textarea { background:var(--bg); border:1px solid var(--border); color:var(--fg); padding:6px 10px; border-radius:3px; font-size:12px; font-family:var(--font); }
input:focus, select:focus { outline:none; border-color:var(--accent); }

/* Cards / Sections */
.card, .section, .tool-section, .hotspot-section, .routing-section, .tunnel-section, .vlan-section, .sim-section { background:var(--bg2); border:1px solid var(--border); border-radius:4px; padding:14px; margin-bottom:12px; }

/* Empty state */
.empty, .empty-state { text-align:center; padding:32px; color:var(--fg3); font-size:13px; }
</style>
