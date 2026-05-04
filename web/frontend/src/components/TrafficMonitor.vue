<template>
  <div class="traffic-section">
    <div class="section-header">
      <h2>Traffic Monitor</h2>
      <span class="refresh-hint">Auto-updating via WebSocket</span>
    </div>
    <div class="charts-grid">
      <div class="card">
        <h3>Sessions Over Time</h3>
        <canvas ref="sessionsChart"></canvas>
      </div>
      <div class="card">
        <h3>Per-Session Bandwidth</h3>
        <table v-if="bwList.length" class="bw-table">
          <thead><tr><th>User</th><th>IP</th><th>RX</th><th>TX</th><th>Total</th></tr></thead>
          <tbody>
            <tr v-for="b in bwList" :key="b.ip">
              <td>{{ b.username }}</td>
              <td class="mono">{{ b.ip }}</td>
              <td class="mono">{{ formatBps(b.rx_bps) }}</td>
              <td class="mono">{{ formatBps(b.tx_bps) }}</td>
              <td class="mono">{{ formatBps(b.rx_bps + b.tx_bps) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">No active sessions</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'

const sessionsChart = ref(null)
const bwList = reactive([])
const prevRx = reactive({})
const prevTx = reactive({})
let chartInstance = null
let refreshTimer = null
let history = []

function formatBps(bps) {
  if (!bps || bps === 0) return '0 bps'
  if (bps < 1000) return bps + ' bps'
  if (bps < 1e6) return (bps / 1e3).toFixed(1) + ' Kbps'
  return (bps / 1e6).toFixed(1) + ' Mbps'
}

function buildChart() {
  if (!sessionsChart.value) return
  chartInstance = new Chart(sessionsChart.value, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Sessions', data: [], borderColor: '#3b82f6', tension: 0.3 }] },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  })
}

async function fetchTraffic() {
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    const svc = data.service || {}
    const sessions = data.sessions || []

    history.push(sessions.length)
    if (history.length > 20) history.shift()
    if (chartInstance) {
      chartInstance.data.labels = history.map((_, i) => `T-${history.length - i}`)
      chartInstance.data.datasets[0].data = [...history]
      chartInstance.update()
    }

    const now = Date.now()
    bwList.length = 0
    for (const s of sessions) {
      const rx = parseInt(s.rx_bytes_raw) || 0
      const tx = parseInt(s.tx_bytes_raw) || 0
      const ip = s.ip || s.sid
      const lastRx = prevRx[ip] || { val: rx, ts: now }
      const lastTx = prevTx[ip] || { val: tx, ts: now }
      const dt = Math.max((now - lastRx.ts) / 1000, 0.1)
      const rxBps = Math.max(0, (rx - lastRx.val) * 8 / dt)
      const txBps = Math.max(0, (tx - lastTx.val) * 8 / dt)
      prevRx[ip] = { val: rx, ts: now }
      prevTx[ip] = { val: tx, ts: now }
      bwList.push({ username: s.username || '-', ip, rx_bps: rxBps, tx_bps: txBps })
    }
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await nextTick()
  buildChart()
  fetchTraffic()
  refreshTimer = setInterval(fetchTraffic, 5000)
})

onUnmounted(() => { clearInterval(refreshTimer); chartInstance?.destroy() })
</script>

<style scoped>
.traffic-section { display: flex; flex-direction: column; gap: 16px; margin-top: 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 18px; }
.refresh-hint { color: #3b82f6; font-size: 12px; }
.charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 15px; margin-bottom: 12px; color: #555; }
.bw-table { width: 100%; border-collapse: collapse; }
.bw-table th, .bw-table td { padding: 6px 8px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
.bw-table th { color: #666; font-weight: 600; font-size: 11px; text-transform: uppercase; }
.mono { font-family: monospace; font-size: 12px; }
.empty { text-align: center; color: #999; padding: 20px; }
</style>
