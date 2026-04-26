<template>
  <div class="sessions-section">
    <div class="section-header">
      <h2>Active Sessions</h2>
      <button class="btn-refresh" @click="$emit('refresh')" :disabled="loading">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
    <table v-if="sessions.length">
      <thead>
        <tr>
          <th>SID</th>
          <th>Interface</th>
          <th>Username</th>
          <th>IP</th>
          <th>Type</th>
          <th>State</th>
          <th>Uptime</th>
          <th>RX</th>
          <th>TX</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in sessions" :key="s.sid">
          <td class="mono">{{ s.sid }}</td>
          <td>{{ s.ifname || '-' }}</td>
          <td>{{ s.username || '-' }}</td>
          <td>{{ s.ip || '-' }}</td>
          <td>{{ s.type || '-' }}</td>
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
defineProps({ sessions: Array, loading: Boolean })
defineEmits(['disconnect', 'refresh'])

function formatBytes(n) {
  if (n === undefined || n === null) return '-'
  if (n < 1024) return n + ' B'
  if (n < 1048576) return (n / 1024).toFixed(1) + ' KB'
  if (n < 1073741824) return (n / 1048576).toFixed(1) + ' MB'
  return (n / 1073741824).toFixed(2) + ' GB'
}

function formatUptime(raw) {
  if (!raw) return '-'
  const s = parseInt(raw)
  if (isNaN(s)) return raw
  if (s < 60) return s + 's'
  if (s < 3600) return Math.floor(s / 60) + 'm'
  if (s < 86400) return Math.floor(s / 3600) + 'h'
  return Math.floor(s / 86400) + 'd'
}
</script>

<style scoped>
.sessions-section { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h2 { font-size: 18px; }
.btn-refresh { padding: 6px 16px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.btn-refresh:disabled { opacity: 0.5; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
th { color: #666; font-weight: 600; text-transform: uppercase; font-size: 12px; }
.mono { font-family: monospace; font-size: 12px; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.badge.active { background: #dcfce7; color: #166534; }
.badge.finishing { background: #fef9c3; color: #854d0e; }
.btn-disconnect { padding: 4px 12px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.btn-disconnect:hover { background: #dc2626; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
