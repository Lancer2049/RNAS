<template>
  <div class="iface-detail" v-if="data">
    <a class="back-link" @click="$emit('back')">← Back to Interfaces</a>
    <h2>{{ data.name }}</h2>

    <div class="detail-grid">
      <div class="d-item"><span class="dl">Status</span><span class="dv" :class="data.running?'up':'down'">{{ data.running ? 'UP' : 'DOWN' }}</span></div>
      <div class="d-item"><span class="dl">MAC</span><span class="dv mono">{{ data.mac || '--' }}</span></div>
      <div class="d-item"><span class="dl">IP</span><span class="dv mono">{{ data.ip || '--' }}</span></div>
      <div class="d-item"><span class="dl">Flags</span><span class="dv mono" style="font-size:10px">{{ data.flags }}</span></div>
      <div class="d-item"><span class="dl">RX</span><span class="dv mono">{{ fmtBytes(data.rx_bytes) }}</span></div>
      <div class="d-item"><span class="dl">TX</span><span class="dv mono">{{ fmtBytes(data.tx_bytes) }}</span></div>
      <div class="d-item"><span class="dl">RX Pkts</span><span class="dv mono">{{ data.rx_packets }}</span></div>
      <div class="d-item"><span class="dl">TX Pkts</span><span class="dv mono">{{ data.tx_packets }}</span></div>
      <div class="d-item"><span class="dl">Errors</span><span class="dv mono" :style="{color: data.rx_errors + data.tx_errors > 0 ? 'var(--red)' : 'inherit'}">{{ data.rx_errors+data.tx_errors }}</span></div>
    </div>

    <h3>Associated Sessions ({{ data.sessions_count }})</h3>
    <table v-if="data.sessions.length">
      <thead><tr><th>User</th><th>IP</th><th>Type</th><th>State</th><th>RX</th><th>TX</th></tr></thead>
      <tbody>
        <tr v-for="s in data.sessions" :key="s.sid">
          <td>{{ s.username }}</td><td class="mono">{{ s.ip }}</td><td>{{ s.type }}</td><td>{{ s.state }}</td><td>{{ s.rx }}</td><td>{{ s.tx }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No active sessions on this interface</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps({ iface: String })
defineEmits(['back'])
const data = ref(null)

function fmtBytes(b) { if (b<1024) return b+'B'; if (b<1048576) return (b/1024).toFixed(1)+'K'; return (b/1048576).toFixed(1)+'M' }

onMounted(async () => {
  try { const r = await fetch(`/api/interfaces/${props.iface}`); data.value = await r.json() } catch {}
})
</script>

<style scoped>
.iface-detail{display:flex;flex-direction:column;gap:14px}
.back-link{color:var(--accent);cursor:pointer;font-size:12px;margin-bottom:4px;display:inline-block}
.back-link:hover{text-decoration:underline}
h2{font-size:16px;color:var(--fg);font-weight:600;font-family:var(--mono)}
.detail-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;background:var(--bg2);padding:14px;border:1px solid var(--border);border-radius:3px}
.d-item{display:flex;flex-direction:column;gap:2px}
.dl{font-size:9px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.dv{font-size:14px;font-weight:700;color:var(--fg)}
.dv.up{color:var(--green)}.dv.down{color:var(--red)}
.mono{font-family:var(--mono)}
h3{font-size:12px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px}
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);font-size:11px}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--fg3);font-size:9px;text-transform:uppercase;letter-spacing:1px;background:var(--bg3)}
.empty{text-align:center;color:var(--fg3);padding:24px;font-size:12px}
</style>
