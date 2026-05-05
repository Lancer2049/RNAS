<template>
  <div class="system-section">
    <h2>System</h2>

    <div class="grid">
      <div class="card" v-for="s in services" :key="s.name">
        <div class="svc-header">
          <span class="svc-name">{{ s.name }}</span>
          <span class="badge" :class="s.active==='active'?'on':'off'">{{ s.active==='active'?'UP':'DOWN' }}</span>
        </div>
        <div class="svc-info">{{ s.desc }}</div>
        <div class="svc-actions">
          <button class="btn-start" @click="svcAction(s.name,'start')" :disabled="acting===s.name">▶</button>
          <button class="btn-stop" @click="svcAction(s.name,'stop')" :disabled="acting===s.name">⏹</button>
          <button class="btn-restart" @click="svcAction(s.name,'restart')" :disabled="acting===s.name">↻</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="log-header">
        <h3>Logs</h3>
        <div class="log-actions">
          <input v-model="logFilter" placeholder="Search logs..." class="filter-input" />
          <button class="btn-refresh" @click="loadLogs">Refresh</button>
        </div>
      </div>
      <pre class="log-area">{{ filteredLogs }}</pre>
    </div>

    <div class="card">
      <h3>System Resources</h3>
      <div class="stat-row"><span>Memory</span><span>{{ mem }}</span></div>
      <div class="stat-row"><span>Disk</span><span>{{ disk }}</span></div>
      <div class="stat-row"><span>Load Average</span><span>{{ loadAvg }}</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const services = ref([])
const logs = ref('')
const logFilter = ref('')
const mem = ref('')
const disk = ref('')
const loadAvg = ref('')
const acting = ref('')

const filteredLogs = computed(() => {
  if (!logFilter.value) return logs.value
  return logs.value.split('\n').filter(l => l.toLowerCase().includes(logFilter.value.toLowerCase())).join('\n')
})

async function loadAll() {
  try {
    const res = await fetch('/api/system/status')
    const d = await res.json()
    services.value = d.services || []
    mem.value = d.memory || ''
    disk.value = d.disk || ''
  } catch {}
}

async function loadLogs() {
  try {
    const res = await fetch('/api/system/logs')
    const d = await res.json()
    logs.value = d.logs || 'No logs'
  } catch {}
}

async function svcAction(name, action) {
  acting.value = name
  try {
    const res = await fetch(`/api/system/service/${name}/${action}`)
    await res.json()
    await new Promise(r => setTimeout(r, 2000))
    await loadAll()
  } catch {}
  acting.value = ''
}

onMounted(() => { loadAll(); loadLogs() })
</script>

<style scoped>
.system-section { display: flex; flex-direction: column; gap: 16px; }
.system-section h2 { font-size: 18px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card h3 { font-size: 14px; color: #555; margin-bottom: 8px; }
.svc-header { display: flex; justify-content: space-between; align-items: center; }
.svc-name { font-weight: 600; font-size: 14px; }
.svc-info { font-size: 11px; color: #888; margin: 4px 0 8px; }
.svc-actions { display: flex; gap: 4px; }
.svc-actions button { padding: 3px 8px; border: 1px solid #ddd; background: #fff; border-radius: 3px; cursor: pointer; font-size: 12px; }
.svc-actions button:hover { background: #f0f4ff; }
.svc-actions button:disabled { opacity: 0.3; }
.btn-start { color: #22c55e; }
.btn-stop { color: #ef4444; }
.btn-restart { color: #f59e0b; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge.on { background: #dcfce7; color: #166534; }
.badge.off { background: #fee2e2; color: #991b1b; }

.log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 12px; }
.log-actions { display: flex; gap: 8px; align-items: center; }
.filter-input { padding: 4px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; width: 180px; }
.btn-refresh { padding: 4px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.log-area { background: #1a1a2e; color: #0f0; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 11px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }
.stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-size: 13px; }
</style>
