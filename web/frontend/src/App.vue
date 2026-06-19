<template>
  <div class="luci-layout">
    <div class="topbar">
      <span class="brand">RNAS</span>
      <span class="hostname">192.168.0.203</span>
      <span class="uptime">{{ service.uptime || '--' }}</span>
      <span class="spacer" />
      <a :href="airosUrl" target="_blank" class="airos-link" :class="{offline: !airosOnline}">
        {{ airosOnline ? 'AirOS' : 'AirOS ⚠' }}
      </a>
    </div>
    <div class="main-area">
      <nav class="sidebar">
        <div class="menu-section">
          <div class="section-title">Monitoring</div>
          <a :class="{active:page==='overview'}" @click="page='overview'" title="System status & traffic">📊 Dashboard</a>
          <a :class="{active:page==='sessions'}" @click="page='sessions'" title="Active PPP connections">
            📋 Sessions <span class="badge" v-if="sessions.length">{{ sessions.length }}</span>
          </a>
          <a :class="{active:page==='proto-monitor'}" @click="page='proto-monitor'" title="Real-time RADIUS protocol events">📡 Protocol</a>
          <a :class="{active:page==='network'}" @click="page='network'" title="Interfaces, routes, ARP, firewall">🌐 Interfaces</a>
        </div>
        <div class="menu-section">
          <div class="section-title">Simulation</div>
          <a :class="{active:page==='subscriber-sim'}" @click="page='subscriber-sim'" title="Simulate multiple CPE clients">👥 Subscribers</a>
          <a :class="{active:page==='scenario-runner'}" @click="page='scenario-runner'" title="One-click preset test scenarios">▶ Scenario</a>
          <a :class="{active:page==='fault-inject'}" @click="page='fault-inject'" title="Simulate network failures">⚠ Fault Inject</a>
        </div>
        <div class="menu-section">
          <div class="section-title">Tools</div>
          <a :class="{active:page==='torch'}" @click="page='torch'" title="Real-time per-session bandwidth">🔥 Torch</a>
          <a :class="{active:page==='queues'}" @click="page='queues'" title="Bandwidth control rules">📏 Queues</a>
          <a :class="{active:page==='sniffer'}" @click="page='sniffer'" title="Capture RADIUS packets">📡 Sniffer</a>
          <a :class="{active:page==='scheduler'}" @click="page='scheduler'" title="Automated test runs">⏰ Scheduler</a>
        </div>
        <div class="menu-section">
          <div class="section-title">RADIUS Tools</div>
          <a :class="{active:page==='radius-editor'}" @click="page='radius-editor'">🔧 Editor</a>
          <a :class="{active:page==='dictionary'}" @click="page='dictionary'">📖 Dictionary</a>
          <a :class="{active:page==='tools'}" @click="page='tools'">🛠 Tools</a>
        </div>
        <div class="menu-section">
          <div class="section-title">Services</div>
          <a :class="{active:page==='services'}" @click="page='services'">⚙️ VPN</a>
          <a :class="{active:page==='proto-config'}" @click="page='proto-config'" title="Configure access protocols">📋 Protocols</a>
          <a :class="{active:page==='config'}" @click="page='config'">📝 Config</a>
        </div>
        <div class="menu-section">
          <div class="section-title">Network</div>
          <a :class="{active:page==='routing'}" @click="page='routing'" title="OSPF / BGP status">🌍 Routing</a>
          <a :class="{active:page==='tunnels'}" @click="page='tunnels'" title="GRE / IPIP / EoIP / VXLAN">🔗 Tunnels</a>
          <a :class="{active:page==='vlans'}" @click="page='vlans'" title="VLAN per User">🏷 VLAN</a>
          <a :class="{active:page==='hotspot'}" @click="page='hotspot'" title="Captive Portal">📶 Hotspot</a>
          <a :class="{active:page==='netflow'}" @click="page='netflow'" title="NetFlow + DHCP Relay">📡 Export</a>
        </div>
        <div class="sidebar-footer">
          <small>RNAS v3.0</small>
        </div>
      </nav>
      <div class="content">
        <div class="breadcrumb">
          {{ breadcrumb }}
        </div>
        <StatusCard v-if="page==='overview'||page==='sessions'" :service="service" />
        <QuickActions v-if="page==='overview'" @nav="page=$event" @refresh="fetchData" />
        <SystemHealth v-if="page==='overview'" />
        <SystemResources v-if="page==='overview'" />
        <ActivityFeed v-if="page==='overview'" />
        <SessionsTable v-if="page==='sessions'||page==='overview'" :sessions="sessions" :loading="loading" @disconnect="handleDisconnect" @refresh="fetchData" @detail="(s) => { selectedSession = s; page = 'session-detail' }" />
        <SessionDetail v-if="page==='session-detail'" :session="selectedSession" @back="page='sessions'" />
        <TrafficMonitor v-if="page==='overview'" />
        <NetworkConfig v-if="page==='network'" />
        <ConfigEditor v-if="page==='config'" />
        <ServicesConfig v-if="page==='services'" />
        <ProtocolConfig v-if="page==='proto-config'" />
        <ToolsPage v-if="page==='tools'" />
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatusCard from './components/StatusCard.vue'
import QuickActions from './components/QuickActions.vue'
import SystemHealth from './components/SystemHealth.vue'
import SystemResources from './components/SystemResources.vue'
import ActivityFeed from './components/ActivityFeed.vue'
import SessionsTable from './components/SessionsTable.vue'
import SessionDetail from './components/SessionDetail.vue'
import NetworkConfig from './components/NetworkConfig.vue'
import TrafficMonitor from './components/TrafficMonitor.vue'
import ConfigEditor from './components/ConfigEditor.vue'
import ServicesConfig from './components/ServicesConfig.vue'
import ProtocolConfig from './components/ProtocolConfig.vue'
import ToolsPage from './components/ToolsPage.vue'
import RADIUSEditor from './components/RADIUSEditor.vue'
import DictionaryBrowser from './components/DictionaryBrowser.vue'
import RoutingPage from './components/RoutingPage.vue'
import TunnelManager from './components/TunnelManager.vue'
import VlanManager from './components/VlanManager.vue'
import HotspotManager from './components/HotspotManager.vue'
import NetflowDhcp from './components/NetflowDhcp.vue'
import SubscriberSim from './components/SubscriberSim.vue'
import ProtoMonitor from './components/ProtoMonitor.vue'
import TrafficTorch from './components/TrafficTorch.vue'
import QueueManager from './components/QueueManager.vue'
import PacketSniffer from './components/PacketSniffer.vue'
import Scheduler from './components/Scheduler.vue'
import ScenarioRunner from './components/ScenarioRunner.vue'
import FaultInject from './components/FaultInject.vue'
import SystemPage from './components/SystemPage.vue'
import TestResults from './components/TestResults.vue'

const page = ref('overview')
const service = ref({ uptime: '--', cpu: '--', mem: '--' })
const sessions = ref([])
const selectedSession = ref(null)
const loading = ref(true)
const airosOnline = ref(false)
const airosUrl = ref('http://192.168.0.202:8000')

const breadcrumb = computed(() => {
  const m = { overview:'Monitoring / Dashboard', sessions:'Monitoring / Sessions', network:'Monitoring / Interfaces', services:'Services / VPN', config:'Services / Configuration', 'radius-editor':'RADIUS / Editor', dictionary:'RADIUS / Dictionary', tools:'RADIUS / Tools', system:'System', 'subscriber-sim':'Simulation / Subscribers', 'scenario-runner':'Simulation / Scenario', 'fault-inject':'Simulation / Fault Inject' }
  return m[page.value] || page.value
})

async function fetchData() {
  loading.value = true
  try { const res = await fetch('/api/status'); const d = await res.json(); service.value = d.service||{}; sessions.value = d.sessions||[] } catch(e){}
  loading.value = false
}
async function checkAirOS() {
  try { const res = await fetch('/api/airos/status'); airosOnline.value = (await res.json()).online||false } catch { airosOnline.value = false }
}
async function handleDisconnect(sid) { await fetch(`/api/sessions/${sid}/disconnect`,{method:'POST'}); fetchData() }

let refreshTimer = null, ws = null
async function startWS() {
  try { ws=new WebSocket(`ws://${location.host}/api/ws`); ws.onmessage=e=>{ try{ const d=JSON.parse(e.data); service.value=d.service||{}; sessions.value=d.sessions||[] }catch{} }; ws.onclose=()=>ws=null; ws.onerror=()=>{ws?.close();ws=null} } catch{ws=null}
}
onMounted(()=>{ fetchData(); checkAirOS(); refreshTimer=setInterval(fetchData,5000); startWS() })
onUnmounted(()=>{ clearInterval(refreshTimer); ws?.close() })
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif; background: #f0f2f5; color: #1a1a2e; font-size: 14px; }
.luci-layout { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 0 20px; height: 46px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; font-size: 13px; flex-shrink: 0; border-bottom: 2px solid #3b82f6; }
.topbar .brand { font-weight: 800; font-size: 16px; letter-spacing: 2px; color: #60a5fa; }
.topbar .hostname { color: #94a3b8; font-family: monospace; }
.topbar .uptime { color: #64748b; font-size: 12px; }
.topbar .spacer { flex: 1; }
.topbar .airos-link { color: #60a5fa; text-decoration: none; font-size: 12px; padding: 2px 10px; border: 1px solid #3b82f6; border-radius: 4px; }
.topbar .airos-link:hover { background: #3b82f6; color: #fff; }
.topbar .airos-link.offline { color: #666; border-color: #444; }

.main-area { display: flex; flex: 1; overflow: hidden; }
.sidebar { width: 210px; background: #1e293b; color: #94a3b8; overflow-y: auto; flex-shrink: 0; display: flex; flex-direction: column; font-size: 13px; }
.sidebar .menu-section { padding: 4px 0; }
.sidebar .section-title { padding: 10px 20px 4px; font-size: 10px; text-transform: uppercase; color: #64748b; letter-spacing: 1.5px; font-weight: 600; }
.sidebar a { display: flex; align-items: center; gap: 10px; padding: 8px 24px; color: #cbd5e1; text-decoration: none; cursor: pointer; transition: all 0.15s; border-left: 3px solid transparent; }
.sidebar a:hover { background: #334155; color: #fff; border-left-color: #475569; }
.sidebar a.active { background: #1e3a5f; color: #60a5fa; font-weight: 600; border-left-color: #3b82f6; }
.sidebar .badge { margin-left: auto; background: #ef4444; color: #fff; padding: 1px 7px; border-radius: 10px; font-size: 10px; font-weight: 700; min-width: 20px; text-align: center; }
.sidebar-footer { margin-top: auto; padding: 12px 20px; color: #475569; font-size: 11px; border-top: 1px solid #334155; }

.content { flex: 1; overflow-y: auto; padding: 20px 28px; background: #f8fafc; }
.breadcrumb { font-size: 11px; color: #94a3b8; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }

/* Global table polish */
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
thead { background: #f8fafc; }
th { color: #64748b; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 12px; text-align: left; border-bottom: 2px solid #e2e8f0; }
td { padding: 9px 12px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
tbody tr:hover { background: #f8faff; }
tbody tr:nth-child(even) { background: #fafbfc; }
tbody tr:nth-child(even):hover { background: #f0f4ff; }

/* Global button polish */
button { font-family: inherit; }
.btn-primary { padding: 6px 14px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 6px 14px; background: #ef4444; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-danger:hover { background: #dc2626; }

/* Global empty state */
.empty-state { text-align: center; padding: 48px 20px; color: #94a3b8; }
.empty-state .icon { font-size: 40px; margin-bottom: 12px; }
.empty-state .text { font-size: 14px; }

/* Global hint text */
.page-hint { font-size: 13px; color: #94a3b8; margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; margin-bottom: 4px; color: #1e293b; }
</style>
