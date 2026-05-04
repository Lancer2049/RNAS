<template>
  <div class="sessions-section">
    <div class="section-header">
      <h2>Active Sessions ({{ sessions.length }})</h2>
      <div class="header-actions">
        <input v-model="filter" placeholder="Filter..." class="filter-input" />
        <button class="btn-refresh" @click="$emit('refresh')" :disabled="loading">{{ loading ? '...' : 'Refresh' }}</button>
        <button class="btn-disconnect-all" @click="disconnectAll" :disabled="!sessions.length">Disconnect All</button>
      </div>
    </div>
    <table v-if="filtered.length">
      <thead>
        <tr>
          <th @click="sortBy='username'" class="sortable">User {{sortBy==='username'?'▾':''}}</th>
          <th @click="sortBy='ip'" class="sortable">IP {{sortBy==='ip'?'▾':''}}</th>
          <th @click="sortBy='type'" class="sortable">Type {{sortBy==='type'?'▾':''}}</th>
          <th @click="sortBy='state'" class="sortable">State {{sortBy==='state'?'▾':''}}</th>
          <th @click="sortBy='uptime_raw'" class="sortable">Uptime {{sortBy==='uptime_raw'?'▾':''}}</th>
          <th>RX</th>
          <th>TX</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in sorted" :key="s.sid">
          <td>{{ s.username || '-' }}</td>
          <td class="mono">{{ s.ip || '-' }}</td>
          <td><span class="type-badge">{{ s.type || '-' }}</span></td>
          <td><span class="badge" :class="s.state">{{ s.state || '-' }}</span></td>
          <td>{{ formatUptime(s.uptime_raw) }}</td>
          <td>{{ formatBytes(s.rx_bytes_raw) }}</td>
          <td>{{ formatBytes(s.tx_bytes_raw) }}</td>
          <td><button class="btn-disconnect" @click="$emit('disconnect', s.sid)">Disconnect</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="!loading" class="empty">No active sessions</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ sessions: Array, loading: Boolean })
defineEmits(['disconnect', 'refresh'])

const filter = ref('')
const sortBy = ref('uptime_raw')

const filtered = computed(() => {
  if (!filter.value) return props.sessions
  const q = filter.value.toLowerCase()
  return props.sessions.filter(s =>
    (s.username||'').toLowerCase().includes(q) ||
    (s.ip||'').includes(q) ||
    (s.type||'').toLowerCase().includes(q)
  )
})

const sorted = computed(() => {
  const key = sortBy.value
  return [...filtered.value].sort((a, b) => {
    const va = a[key], vb = b[key]
    if (va == null) return 1
    if (vb == null) return -1
    if (typeof va === 'number') return va - vb
    return String(va).localeCompare(String(vb))
  })
})

async function disconnectAll() {
  for (const s of props.sessions) {
    await fetch(`/api/sessions/${s.sid}/disconnect`, { method: 'POST' })
  }
  location.reload()
}

function formatBytes(n) {
  if (!n) return '0 B'
  if (n < 1024) return n + ' B'
  if (n < 1e6) return (n/1024).toFixed(1)+' KB'
  return (n/1e6).toFixed(1)+' MB'
}
function formatUptime(raw) {
  if (!raw) return '-'
  const s = parseInt(raw)
  if (isNaN(s)) return raw
  if (s < 60) return s+'s'
  if (s < 3600) return Math.floor(s/60)+'m'
  if (s < 86400) return Math.floor(s/3600)+'h'
  return Math.floor(s/86400)+'d'
}
</script>

<style scoped>
.sessions-section { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.section-header h2 { font-size: 16px; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.filter-input { padding: 4px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; width: 150px; }
.btn-refresh { padding: 4px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-refresh:disabled { opacity: 0.5; }
.btn-disconnect-all { padding: 4px 12px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-disconnect-all:disabled { opacity: 0.5; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { color: #666; font-weight: 600; font-size: 11px; text-transform: uppercase; cursor: default; }
th.sortable { cursor: pointer; }
th.sortable:hover { color: #3b82f6; }
.mono { font-family: monospace; font-size: 12px; }
.type-badge { background: #f0f4ff; color: #3b82f6; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.badge.active { background: #dcfce7; color: #166534; }
.badge.finishing, .badge.finish { background: #fef9c3; color: #854d0e; }
.btn-disconnect { padding: 3px 10px; background: #ef4444; color: #fff; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; }
.btn-disconnect:hover { background: #dc2626; }
.empty { text-align: center; color: #999; padding: 30px; }
</style>
