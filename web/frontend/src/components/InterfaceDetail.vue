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

    <div class="hist-block">
      <h3 class="hist-title">
        Traffic History
        <span class="range-btns">
          <button :class="{sel: period==='5m'}" @click="setPeriod('5m')">5m</button>
          <button :class="{sel: period==='1h'}" @click="setPeriod('1h')">1h</button>
          <button :class="{sel: period==='1d'}" @click="setPeriod('1d')">1d</button>
          <button :class="{sel: period==='1w'}" @click="setPeriod('1w')">1w</button>
        </span>
      </h3>
      <canvas ref="histChart" class="hist-canvas"></canvas>
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
const props = defineProps({ iface: String })
defineEmits(['back'])
const data = ref(null)
const histChart = ref(null)
const period = ref('1h')
let histChartInst = null, timer = null

function fmtBytes(b) { if (b<1024) return b+'B'; if (b<1048576) return (b/1024).toFixed(1)+'K'; return (b/1048576).toFixed(1)+'M' }

async function fetchHistory() {
  try {
    const r = await fetch(`/api/traffic/history?interface=${props.iface}&period=${period.value}`)
    if (!r.ok) return
    const d = await r.json()
    const pts = d.data || []
    if (histChartInst) {
      const showDate = period.value === '1d' || period.value === '1w'
      histChartInst.data.labels = pts.map(p => {
        const dt = new Date(p.ts * 1000)
        return showDate ? `${dt.getMonth() + 1}/${dt.getDate()} ${dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : dt.toLocaleTimeString()
      })
      histChartInst.data.datasets = [
        { label: 'RX', data: pts.map(p => p.rx), borderColor: '#0abde3', backgroundColor: 'transparent', tension: 0.3, borderWidth: 1.5 },
        { label: 'TX', data: pts.map(p => p.tx), borderColor: '#10ac84', backgroundColor: 'transparent', tension: 0.3, borderWidth: 1.5 },
      ]
      histChartInst.update('none')
    }
  } catch {}
}

function setPeriod(p) { period.value = p; fetchHistory() }

onMounted(async () => {
  try { const r = await fetch(`/api/interfaces/${props.iface}`); data.value = await r.json() } catch {}
  await nextTick()
  if (histChart.value) {
    histChartInst = new Chart(histChart.value, {
      type: 'line',
      data: { labels: [], datasets: [] },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(46,64,82,0.3)' }, ticks: { color: '#8395a7', callback: v => v < 1e6 ? (v/1e3).toFixed(0)+'K' : (v/1e6).toFixed(1)+'M' } },
          x: { ticks: { color: '#576574', maxTicksLimit: 8, font: { size: 9 } }, grid: { display: false } }
        },
        plugins: { legend: { position: 'bottom', labels: { color: '#8395a7', font: { size: 10 }, usePointStyle: true, padding: 12 } } }
      }
    })
    fetchHistory()
  }
  timer = setInterval(fetchHistory, 15000)
})
onUnmounted(() => { clearInterval(timer); histChartInst?.destroy() })
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
.hist-block{background:var(--bg2);border:1px solid var(--border);padding:12px 14px;border-radius:3px}
.hist-title{display:flex;align-items:center;font-size:12px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.hist-canvas{max-height:200px}
.range-btns{margin-left:auto;display:inline-flex;gap:2px}
.range-btns button{padding:2px 8px;background:var(--bg3);color:var(--fg2);border:1px solid var(--border);border-radius:2px;cursor:pointer;font-size:9px;font-family:var(--font)}
.range-btns button.sel{background:var(--accent);color:#000;border-color:var(--accent)}
.range-btns button:hover:not(.sel){border-color:var(--accent);color:var(--fg)}
</style>
