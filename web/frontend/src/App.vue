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
          <div class="section-title">Status</div>
          <a :class="{active:page==='overview'}" @click="page='overview'">📊 Overview</a>
          <a :class="{active:page==='sessions'}" @click="page='sessions'">
            📋 Sessions <span class="badge" v-if="sessions.length">{{ sessions.length }}</span>
          </a>
        </div>
        <div class="menu-section">
          <div class="section-title">Network</div>
          <a :class="{active:page==='network'}" @click="page='network'">🌐 Interfaces</a>
        </div>
        <div class="menu-section">
          <div class="section-title">AAA</div>
          <a :class="{active:page==='aaa-users'}" @click="page='aaa-users'">👥 Users</a>
          <a :class="{active:page==='auth-logs'}" @click="page='auth-logs'">📜 Auth Logs</a>
          <a :class="{active:page==='acct-records'}" @click="page='acct-records'">📊 Accounting</a>
          <a :class="{active:page==='user-groups'}" @click="page='user-groups'">👥 Groups</a>
          <a :class="{active:page==='nas-list'}" @click="page='nas-list'">🖥 NAS</a>
        </div>
        <div class="menu-section">
          <div class="section-title">Services</div>
          <a :class="{active:page==='services'}" @click="page='services'">⚙️ VPN</a>
          <a :class="{active:page==='config'}" @click="page='config'">📝 Config</a>
        </div>
        <div class="menu-section">
          <div class="section-title">RADIUS</div>
          <a :class="{active:page==='radius-editor'}" @click="page='radius-editor'">🔧 Editor</a>
          <a :class="{active:page==='dictionary'}" @click="page='dictionary'">📖 Dictionary</a>
          <a :class="{active:page==='tools'}" @click="page='tools'">🛠 Tools</a>
        </div>
        <div class="menu-section">
          <div class="section-title">System</div>
          <a :class="{active:page==='system'}" @click="page='system'">💻 System</a>
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
        <SessionsTable v-if="page==='sessions'||page==='overview'" :sessions="sessions" :loading="loading" @disconnect="handleDisconnect" @refresh="fetchData" />
        <TrafficMonitor v-if="page==='overview'" />
        <NetworkConfig v-if="page==='network'" />
        <ConfigEditor v-if="page==='config'" />
        <ServicesConfig v-if="page==='services'" />
        <ToolsPage v-if="page==='tools'" />
        <RADIUSEditor v-if="page==='radius-editor'" />
        <DictionaryBrowser v-if="page==='dictionary'" />
        <AAAUsers v-if="page==='aaa-users'" />
        <AuthLogs v-if="page==='auth-logs'" />
        <AcctRecords v-if="page==='acct-records'" />
        <UserGroups v-if="page==='user-groups'" />
        <NASClients v-if="page==='nas-list'" />
        <SystemPage v-if="page==='system'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatusCard from './components/StatusCard.vue'
import SessionsTable from './components/SessionsTable.vue'
import NetworkConfig from './components/NetworkConfig.vue'
import TrafficMonitor from './components/TrafficMonitor.vue'
import ConfigEditor from './components/ConfigEditor.vue'
import ServicesConfig from './components/ServicesConfig.vue'
import ToolsPage from './components/ToolsPage.vue'
import RADIUSEditor from './components/RADIUSEditor.vue'
import DictionaryBrowser from './components/DictionaryBrowser.vue'
import AAAUsers from './components/AAAUsers.vue'
import AuthLogs from './components/AuthLogs.vue'
import AcctRecords from './components/AcctRecords.vue'
import UserGroups from './components/UserGroups.vue'
import NASClients from './components/NASClients.vue'
import SystemPage from './components/SystemPage.vue'

const page = ref('overview')
const service = ref({ uptime: '--', cpu: '--', mem: '--' })
const sessions = ref([])
const loading = ref(true)
const airosOnline = ref(false)
const airosUrl = ref('http://192.168.0.202:8000')

const breadcrumb = computed(() => {
  const m = { overview:'Status / Overview', sessions:'Status / Sessions', network:'Network / Interfaces', services:'Services / VPN', config:'Services / Configuration', 'radius-editor':'RADIUS / Editor', dictionary:'RADIUS / Dictionary', tools:'RADIUS / Tools', system:'System', 'aaa-users':'AAA / Users', 'auth-logs':'AAA / Auth Logs', 'acct-records':'AAA / Accounting', 'user-groups':'AAA / Groups', 'nas-list':'AAA / NAS Clients' }
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
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f0f2f5; color: #333; overflow: hidden; }
.luci-layout { display: flex; flex-direction: column; height: 100vh; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 0 20px; height: 44px; background: #1a1a2e; color: #fff; font-size: 13px; flex-shrink: 0; }
.topbar .brand { font-weight: 700; font-size: 15px; letter-spacing: 1px; }
.topbar .hostname { color: #8ab4f8; }
.topbar .uptime { color: #888; font-size: 12px; }
.topbar .spacer { flex: 1; }
.topbar .airos-link { color: #8ab4f8; text-decoration: none; font-size: 12px; }
.topbar .airos-link.offline { color: #666; }

.main-area { display: flex; flex: 1; overflow: hidden; }
.sidebar { width: 200px; background: #2b2d42; color: #ccc; overflow-y: auto; flex-shrink: 0; display: flex; flex-direction: column; font-size: 13px; }
.sidebar .menu-section { padding: 8px 0; }
.sidebar .section-title { padding: 6px 16px; font-size: 10px; text-transform: uppercase; color: #666; letter-spacing: 1px; }
.sidebar a { display: flex; align-items: center; gap: 8px; padding: 8px 20px; color: #bbb; text-decoration: none; cursor: pointer; transition: background .15s; }
.sidebar a:hover { background: #3a3d56; color: #fff; }
.sidebar a.active { background: #3b82f6; color: #fff; font-weight: 600; }
.sidebar .badge { margin-left: auto; background: #ef4444; color: #fff; padding: 1px 6px; border-radius: 8px; font-size: 11px; min-width: 18px; text-align: center; }
.sidebar-footer { margin-top: auto; padding: 10px 16px; color: #555; font-size: 11px; }

.content { flex: 1; overflow-y: auto; padding: 16px 24px; }
.breadcrumb { font-size: 11px; color: #999; margin-bottom: 12px; }
</style>
