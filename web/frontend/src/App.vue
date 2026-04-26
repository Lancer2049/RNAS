<template>
  <div class="dashboard">
    <header>
      <h1>RNAS Dashboard</h1>
      <span class="version">v2.0</span>
    </header>
    <StatusCard :service="service" />
    <SessionsTable
      :sessions="sessions"
      :loading="loading"
      @disconnect="handleDisconnect"
      @refresh="fetchData"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatusCard from './components/StatusCard.vue'
import SessionsTable from './components/SessionsTable.vue'

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
header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 24px; }
header h1 { font-size: 24px; color: #1a1a2e; }
.version { font-size: 14px; color: #888; }
</style>
