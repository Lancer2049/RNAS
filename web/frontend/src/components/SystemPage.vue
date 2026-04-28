<template>
  <div class="system-section">
    <h2>System Status</h2>

    <div class="grid">
      <div class="card" v-for="s in services" :key="s.name">
        <div class="svc-header">
          <span class="svc-name">{{ s.name }}</span>
          <span class="badge" :class="s.active === 'active' ? 'on' : 'off'">{{ s.active === 'active' ? 'UP' : 'DOWN' }}</span>
        </div>
        <div class="svc-info">{{ s.desc }}</div>
      </div>
    </div>

    <div class="card">
      <h3>Recent Logs</h3>
      <button class="btn-refresh" @click="loadLogs">Refresh</button>
      <pre class="log-area">{{ logs }}</pre>
    </div>

    <div class="card">
      <h3>Memory / Disk</h3>
      <div class="stat-row"><span>Memory</span><span>{{ mem }}</span></div>
      <div class="stat-row"><span>Disk</span><span>{{ disk }}</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const services = ref([])
const logs = ref('')
const mem = ref('')
const disk = ref('')

async function loadAll() {
  const res = await fetch('/api/system/status')
  const d = await res.json()
  services.value = d.services || []
  mem.value = d.memory || ''
  disk.value = d.disk || ''
}

async function loadLogs() {
  const res = await fetch('/api/system/logs')
  const d = await res.json()
  logs.value = d.logs || 'No logs'
}

onMounted(() => { loadAll(); loadLogs() })
</script>

<style scoped>
.system-section { display: flex; flex-direction: column; gap: 16px; }
.system-section h2 { font-size: 18px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 14px; color: #555; margin-bottom: 8px; }
.svc-header { display: flex; justify-content: space-between; align-items: center; }
.svc-name { font-weight: 600; font-size: 14px; }
.svc-info { font-size: 12px; color: #888; margin-top: 4px; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge.on { background: #dcfce7; color: #166534; }
.badge.off { background: #fee2e2; color: #991b1b; }
.btn-refresh { padding: 4px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-bottom: 8px; }
.log-area { background: #1a1a2e; color: #0f0; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 11px; max-height: 200px; overflow-y: auto; white-space: pre-wrap; }
.stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-size: 13px; }
</style>
