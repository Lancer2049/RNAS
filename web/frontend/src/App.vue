<template>
  <div class="dashboard">
    <header>
      <h1>RNAS Dashboard</h1>
      <span class="version">v2.0</span>
    </header>
    <nav class="tabs">
      <button :class="{ active: tab === 'overview' }" @click="tab = 'overview'">Overview</button>
      <button :class="{ active: tab === 'sessions' }" @click="tab = 'sessions'">Sessions</button>
      <button :class="{ active: tab === 'network' }" @click="tab = 'network'">Network</button>
      <button :class="{ active: tab === 'config' }" @click="tab = 'config'">Config</button>
      <button :class="{ active: tab === 'services' }" @click="tab = 'services'">Services</button>
    </nav>
    <StatusCard v-if="tab === 'overview' || tab === 'sessions'" :service="service" />
    <SessionsTable
      v-if="tab === 'sessions' || tab === 'overview'"
      :sessions="sessions"
      :loading="loading"
      @disconnect="handleDisconnect"
      @refresh="fetchData"
    />
    <NetworkConfig v-if="tab === 'network'" />
    <TrafficMonitor v-if="tab === 'overview'" />
    <ConfigEditor v-if="tab === 'config'" />
    <ServicesConfig v-if="tab === 'services'" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatusCard from './components/StatusCard.vue'
import SessionsTable from './components/SessionsTable.vue'
import NetworkConfig from './components/NetworkConfig.vue'
import TrafficMonitor from './components/TrafficMonitor.vue'
import ConfigEditor from './components/ConfigEditor.vue'
import ServicesConfig from './components/ServicesConfig.vue'

const tab = ref('overview')
const service = ref({ uptime: '--', cpu: '--', mem: '--' })
const sessions = ref([])
const loading = ref(true)

async function fetchData() {
  loading.value = true
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    service.value = data.service || {}
    sessions.value = data.sessions || []
  } catch (e) {
    console.error('API error:', e)
  }
  loading.value = false
}

async function handleDisconnect(sid) {
  await fetch(`/api/sessions/${sid}/disconnect`, { method: 'POST' })
  fetchData()
}

onMounted(fetchData)
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f0f2f5; color: #333; }
.dashboard { max-width: 1200px; margin: 0 auto; padding: 24px; }
header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px; }
header h1 { font-size: 24px; color: #1a1a2e; }
.version { font-size: 14px; color: #888; }
nav.tabs { display: flex; gap: 4px; margin-bottom: 24px; }
nav.tabs button { padding: 8px 20px; border: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 14px; background: #e5e7eb; color: #555; }
nav.tabs button.active { background: #fff; color: #1a1a2e; font-weight: 600; box-shadow: 0 -2px 4px rgba(0,0,0,0.05); }
</style>
