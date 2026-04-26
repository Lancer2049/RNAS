<template>
  <div class="traffic-section">
    <div class="section-header">
      <h2>Traffic Monitor</h2>
      <button class="btn-refresh" @click="fetchTraffic" :disabled="loading">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
    <div class="charts-grid">
      <div class="card">
        <h3>Sessions Over Time</h3>
        <canvas ref="sessionsChart"></canvas>
      </div>
      <div class="card">
        <h3>RADIUS Auth Requests</h3>
        <div class="stat-grid">
          <div class="stat">
            <span class="stat-label">Auth Sent</span>
            <span class="stat-value">{{ traffic.auth_sent || 0 }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Acct Sent</span>
            <span class="stat-value">{{ traffic.acct_sent || 0 }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Fail Count</span>
            <span class="stat-value" :class="{ 'text-red': traffic.radius_fail_count > 0 }">{{ traffic.radius_fail_count || 0 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'

const loading = ref(false)
const sessionsChart = ref(null)
const traffic = reactive({ auth_sent: 0, acct_sent: 0, radius_fail_count: 0 })

let chartInstance = null
let refreshTimer = null
let history = []

function buildChart() {
  if (!sessionsChart.value) return
  const ctx = sessionsChart.value.getContext('2d')
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Sessions', data: [], borderColor: '#3b82f6', tension: 0.3 }] },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  })
}

async function fetchTraffic() {
  loading.value = true
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    const svc = data.service || {}
    traffic.auth_sent = svc.auth_sent
    traffic.acct_sent = svc.acct_sent
    traffic.radius_fail_count = svc.radius_fail_count

    const count = data.sessions_count || 0
    history.push(count)
    if (history.length > 20) history.shift()

    if (chartInstance) {
      chartInstance.data.labels = history.map((_, i) => `T-${history.length - i}`)
      chartInstance.data.datasets[0].data = [...history]
      chartInstance.update()
    }
  } catch (e) { console.error(e) }
  loading.value = false
}

onMounted(async () => {
  await nextTick()
  const ChartJS = await import('chart.js/auto')
  window.Chart = ChartJS.default
  buildChart()
  fetchTraffic()
  refreshTimer = setInterval(fetchTraffic, 10000)
})

onUnmounted(() => { clearInterval(refreshTimer); chartInstance?.destroy() })
</script>

<style scoped>
.traffic-section { display: flex; flex-direction: column; gap: 16px; margin-top: 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 18px; }
.btn-refresh { padding: 6px 16px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 15px; margin-bottom: 12px; color: #555; }
.stat-grid { display: flex; flex-direction: column; gap: 16px; }
.stat { display: flex; justify-content: space-between; align-items: center; }
.stat-label { font-size: 13px; color: #888; }
.stat-value { font-size: 22px; font-weight: 600; }
.text-red { color: #ef4444; }
</style>
