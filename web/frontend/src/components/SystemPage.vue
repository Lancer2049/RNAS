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
.system-section { display: flex; flex-direction: column; gap: 14px; }
.system-section h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
.card { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.card h3 { font-size: 12px; color: var(--fg2); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.svc-header { display: flex; justify-content: space-between; align-items: center; }
.svc-name { font-weight: 600; font-size: 13px; color: var(--fg); font-family: var(--mono); }
.svc-info { font-size: 10px; color: var(--fg3); margin: 4px 0 8px; }
.svc-actions { display: flex; gap: 4px; }
.svc-actions button { padding: 3px 8px; border: 1px solid var(--border); background: var(--bg); border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.svc-actions button:hover { background: var(--bg3); }
.svc-actions button:disabled { opacity: 0.3; }
.btn-start { color: var(--green); } .btn-stop { color: var(--red); } .btn-restart { color: #ff9f43; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; }
.badge.on { background: rgba(16,172,132,0.12); color: var(--green); }
.badge.off { background: rgba(238,82,83,0.12); color: var(--red); }
.log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 12px; }
.log-actions { display: flex; gap: 8px; align-items: center; }
.filter-input { padding: 4px 10px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; width: 180px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; }
.filter-input:focus { border-color: var(--accent); }
.btn-refresh { padding: 4px 12px; background: var(--bg3); color: var(--accent); border: 1px solid var(--accent); border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.btn-refresh:hover { background: var(--accent); color: #000; }
.log-area { background: #0a0f14; color: var(--green); padding: 12px; border-radius: 3px; font-family: var(--mono); font-size: 11px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; border: 1px solid var(--border); }
.stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 12px; color: var(--fg); }
</style>
