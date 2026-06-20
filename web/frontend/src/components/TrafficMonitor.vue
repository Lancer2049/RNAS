<template>
  <div class="traffic-page">
    <!-- Interface Bandwidth -->
    <div class="if-section">
      <h3 class="sec-title">Interface Bandwidth</h3>
      <table class="if-table">
        <thead><tr><th>Name</th><th>Rate RX</th><th>Rate TX</th><th>Total RX</th><th>Total TX</th><th>Pkts</th><th>Err</th></tr></thead>
        <tbody>
          <tr v-for="iface in ifaces" :key="iface.name" :class="{down: !iface.running}">
            <td class="mono">{{ iface.name }}</td>
            <td class="mono rate-rx">{{ formatBps(iface.rx_rate) }}</td>
            <td class="mono rate-tx">{{ formatBps(iface.tx_rate) }}</td>
            <td class="mono">{{ fmtBytes(iface.rx_bytes) }}</td>
            <td class="mono">{{ fmtBytes(iface.tx_bytes) }}</td>
            <td class="mono">{{ iface.rx_packets + iface.tx_packets }}</td>
            <td><span :class="{err: (iface.rx_errors + iface.tx_errors) > 0}">{{ iface.rx_errors + iface.tx_errors }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Session Bandwidth -->
    <div class="if-section">
      <h3 class="sec-title">Per-Session Bandwidth</h3>
      <table v-if="bwList.length" class="if-table">
        <thead><tr><th>User</th><th>IP</th><th>RX</th><th>TX</th><th>Total</th></tr></thead>
        <tbody>
          <tr v-for="b in bwList" :key="b.ip">
            <td>{{ b.username || '-' }}</td>
            <td class="mono">{{ b.ip }}</td>
            <td class="mono">{{ formatBps(b.rx_bps) }}</td>
            <td class="mono">{{ formatBps(b.tx_bps) }}</td>
            <td class="mono">{{ formatBps(b.rx_bps + b.tx_bps) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">No active sessions</div>
    </div>

    <!-- Interface Rate Chart -->
    <div class="if-section">
      <h3 class="sec-title">Interface Rate (bps)</h3>
      <canvas ref="ifaceChart" style="max-height:220px"></canvas>
    </div>

    <!-- Session History Chart -->
    <div class="if-section">
      <h3 class="sec-title">Sessions Over Time</h3>
      <canvas ref="sessionsChart" style="max-height:180px"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'

const sessionsChart = ref(null), ifaceChart = ref(null)
const ifaces = ref([])
const bwList = reactive([])
const prevIfaceRx = reactive({}), prevIfaceTs = reactive({})
const prevRx = reactive({}), prevTx = reactive({})
let chartInstance = null, ifaceChartInst = null, timer = null, history = []
const ifaceHistory = reactive({})
const COLORS = ['#0abde3','#10ac84','#ff9f43','#ee5253','#5f27cd','#f368e0','#01a3a4','#54a0ff']

function fmtBytes(b) {
  if (b < 1024) return b + ' B'
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
  if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB'
  return (b / 1073741824).toFixed(2) + ' GB'
}

function formatBps(bps) {
  if (!bps || bps === 0) return '0 bps'
  if (bps < 1000) return bps + ' bps'
  if (bps < 1e6) return (bps / 1e3).toFixed(1) + ' Kbps'
  return (bps / 1e6).toFixed(1) + ' Mbps'
}

async function fetchAll() {
  try {
    const [ifRes, statusRes] = await Promise.all([
      fetch('/api/interfaces'),
      fetch('/api/status')
    ])
    const ifData = await ifRes.json()
    const stData = await statusRes.json()
    ifaces.value = ifData.interfaces || []
    const sessions = stData.sessions || []

    // Interface rate calculation
    const now = Date.now()
    for (const iface of ifaces.value) {
      const n = iface.name
      if (n === 'lo') continue
      if (!ifaceHistory[n]) ifaceHistory[n] = { rx: [], tx: [], labels: [] }
      const h = ifaceHistory[n]
      const prevRxV = prevIfaceRx[n+"_rx"] || iface.rx_bytes
      const prevTxV = prevIfaceRx[n+"_tx"] || iface.tx_bytes
      const prevTs = prevIfaceTs[n] || now - 5000
      const dt = Math.max((now - prevTs) / 1000, 0.1)
      const rxRate = Math.max(0, (iface.rx_bytes - prevRxV) * 8 / dt)
      const txRate = Math.max(0, (iface.tx_bytes - prevTxV) * 8 / dt)
      prevIfaceRx[n+"_rx"] = iface.rx_bytes
      prevIfaceRx[n+"_tx"] = iface.tx_bytes
      prevIfaceTs[n] = now
      iface.rx_rate = rxRate; iface.tx_rate = txRate // table display
      h.rx.push(rxRate); h.tx.push(txRate)
      h.labels.push(new Date().toLocaleTimeString())
      if (h.rx.length > 40) { h.rx.shift(); h.tx.shift(); h.labels.shift() }
    }
    if (ifaceChartInst) {
      const names = ifaces.value.filter(i => i.name !== 'lo').map(i => i.name)
      const datasets = []
      let ci = 0
      for (const n of names) {
        const d = ifaceHistory[n] || { rx: [], tx: [], labels: [] }
        datasets.push({ label: n + ' RX', data: d.rx, borderColor: COLORS[ci % COLORS.length], backgroundColor: 'transparent', tension: 0.2, borderWidth: 1.5 })
        datasets.push({ label: n + ' TX', data: d.tx, borderColor: COLORS[(ci + 1) % COLORS.length], backgroundColor: 'transparent', tension: 0.2, borderWidth: 1, borderDash: [3, 3] })
        ci += 2
      }
      ifaceChartInst.data.datasets = datasets
      ifaceChartInst.data.labels = (ifaceHistory[names[0]] || ifaceHistory[Object.keys(ifaceHistory)[0]] || {}).labels || []
      ifaceChartInst.update('none')
    }

    history.push(sessions.length)
    if (history.length > 40) history.shift()
    if (chartInstance) {
      chartInstance.data.labels = history.map((_, i) => `T-${history.length - i}`)
      chartInstance.data.datasets[0].data = [...history]
      chartInstance.update('none')
    }

    bwList.length = 0
    for (const s of sessions) {
      const rx = parseInt(s.rx_bytes_raw) || 0, tx = parseInt(s.tx_bytes_raw) || 0
      const ip = s.ip || s.sid
      const lr = prevRx[ip] || { val: rx, ts: now }
      const lt = prevTx[ip] || { val: tx, ts: now }
      const dt = Math.max((now - lr.ts) / 1000, 0.1)
      prevRx[ip] = { val: rx, ts: now }; prevTx[ip] = { val: tx, ts: now }
      bwList.push({ username: s.username || '-', ip, rx_bps: Math.max(0, (rx - lr.val) * 8 / dt), tx_bps: Math.max(0, (tx - lt.val) * 8 / dt) })
    }
  } catch {}
}

onMounted(async () => {
  await nextTick()
  if (sessionsChart.value) {
    chartInstance = new Chart(sessionsChart.value, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Sessions', data: [], borderColor: '#0abde3', backgroundColor: 'rgba(10,189,227,0.1)', fill: true, tension: 0.3 }] },
      options: { responsive: true, scales: { y: { beginAtZero: true, grid: { color: 'rgba(46,64,82,0.3)' } }, x: { display: false } }, plugins: { legend: { display: false } } }
    })
  }
  if (ifaceChart.value) {
    ifaceChartInst = new Chart(ifaceChart.value, {
      type: 'line',
      data: { labels: [], datasets: [] },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(46,64,82,0.3)' }, ticks: { color: '#8395a7', callback: v => v < 1e6 ? (v/1e3).toFixed(0)+'K' : (v/1e6).toFixed(1)+'M' } },
          x: { ticks: { color: '#576574', maxTicksLimit: 8, font: { size: 9 } }, grid: { display: false } }
        },
        plugins: { legend: { position: 'bottom', labels: { color: '#8395a7', font: { size: 10 }, usePointStyle: true, padding: 12 } } },
        interaction: { intersect: false, mode: 'index' }
      }
    })
  }
  fetchAll(); timer = setInterval(fetchAll, 5000)
})
onUnmounted(() => { clearInterval(timer); chartInstance?.destroy(); ifaceChartInst?.destroy() })
</script>

<style scoped>
.traffic-page { display: flex; flex-direction: column; gap: 16px; }
.sec-title { font-size: 13px; text-transform: uppercase; color: var(--fg2); letter-spacing: 1px; margin-bottom: 8px; padding-left: 2px; }
.if-section { background: var(--bg2); border: 1px solid var(--border); padding: 12px 14px; border-radius: 3px; }
.if-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.if-table th { text-align: left; color: var(--fg3); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; padding: 4px 8px; border-bottom: 1px solid var(--border); }
.if-table td { padding: 4px 8px; border-bottom: 1px solid rgba(46,64,82,0.3); }
.if-table tr.down { opacity: 0.4; }
.mono { font-family: var(--mono); font-size: 11px; }
.rate-rx { color: var(--accent); } .rate-tx { color: var(--green); }
.err { color: var(--red); font-weight: 600; }
.empty { text-align: center; color: var(--fg3); padding: 16px; font-size: 12px; }
</style>
