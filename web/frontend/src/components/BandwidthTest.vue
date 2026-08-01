<template>
  <div class="bw-section">
    <h2>Bandwidth Test</h2>
    <p class="hint">iperf3 throughput test — run <code>iperf3 -s</code> on target first</p>

    <div class="bw-form">
      <div class="field"><label>Target</label><input v-model="target" placeholder="192.168.0.203" @keyup.enter="runTest" /></div>
      <div class="field"><label>Port</label><input v-model.number="port" type="number" min="1" max="65535" /></div>
      <div class="field"><label>Duration</label><select v-model.number="duration"><option :value="3">3s</option><option :value="5">5s</option><option :value="10">10s</option><option :value="30">30s</option></select></div>
      <div class="field"><label>Proto</label><select v-model="proto"><option value="tcp">TCP</option><option value="udp">UDP</option></select></div>
      <button class="btn-start" @click="runTest" :disabled="running">{{ running ? 'Testing...' : '▶ Start' }}</button>
      <button v-if="running" class="btn-stop" @click="running=false">⏹ Stop</button>
    </div>

    <div v-if="result" class="bw-results">
      <div class="res-card" :class="result.ok ? 'ok' : 'fail'">
        <h3>{{ result.ok ? '✓ Test Complete' : '✕ Test Failed' }}</h3>
        <template v-if="result.ok">
          <div class="res-grid">
            <div class="res-item"><span class="rl">TX</span><span class="rv mono">{{ result.sent_mbps }} Mbps</span></div>
            <div class="res-item"><span class="rl">RX</span><span class="rv mono">{{ result.recv_mbps }} Mbps</span></div>
            <div class="res-item"><span class="rl">Retrans</span><span class="rv">{{ result.retransmits || 0 }}</span></div>
            <div class="res-item" v-if="result.jitter_ms"><span class="rl">Jitter</span><span class="rv mono">{{ result.jitter_ms }} ms</span></div>
            <div class="res-item" v-if="result.lost_packets"><span class="rl">Lost</span><span class="rv mono">{{ result.lost_packets }} pkts</span></div>
            <div class="res-item"><span class="rl">Target</span><span class="rv mono">{{ result.target }}:{{ result.port }}</span></div>
          </div>
        </template>
        <div v-else class="err-msg">{{ result.error }}</div>
      </div>
    </div>

    <div v-if="history.length" class="bw-history">
      <h3>History</h3>
      <table>
        <thead><tr><th>Time</th><th>Target</th><th>TX Mbps</th><th>RX Mbps</th><th>Proto</th></tr></thead>
        <tbody>
          <tr v-for="h in history" :key="h.time">
            <td class="mono">{{ h.time }}</td><td class="mono">{{ h.target }}:{{ h.port }}</td>
            <td class="mono">{{ h.sent_mbps || '--' }}</td><td class="mono">{{ h.recv_mbps || '--' }}</td>
            <td>{{ h.proto.toUpperCase() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const target = ref('192.168.0.203'), port = ref(5201), duration = ref(5), proto = ref('tcp')
const running = ref(false), result = ref(null), history = ref([])

async function runTest() {
  if (!target.value.trim()) return
  running.value = true; result.value = null
  try {
    const r = await fetch('/api/tools/bandwidth', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: target.value.trim(), port: port.value, duration: duration.value, proto: proto.value })
    })
    const d = await r.json()
    result.value = d
    if (d.ok) {
      history.value.unshift({
        time: new Date().toLocaleTimeString(),
        target: d.target, port: d.port, sent_mbps: d.sent_mbps, recv_mbps: d.recv_mbps, proto: d.proto
      })
      if (history.value.length > 20) history.value.length = 20
    }
  } catch (e) {
    result.value = { ok: false, error: 'Network error: ' + e.message }
  }
  running.value = false
}
</script>

<style scoped>
.bw-section { display: flex; flex-direction: column; gap: 14px; }
h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.hint { font-size: 11px; color: var(--fg3); }
.hint code { background: var(--bg3); padding: 1px 6px; border-radius: 3px; font-family: var(--mono); color: var(--accent); }
.bw-form { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; background: var(--bg2); padding: 12px; border: 1px solid var(--border); border-radius: 3px; }
.field { display: flex; flex-direction: column; gap: 2px; }
.field label { font-size: 9px; color: var(--fg3); text-transform: uppercase; letter-spacing: 1px; }
.field input, .field select { padding: 5px 8px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; width: 100px; }
.field input:focus, .field select:focus { border-color: var(--accent); }
.btn-start { padding: 6px 16px; background: var(--green); color: #000; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; font-weight: 600; font-family: var(--font); }
.btn-start:disabled { opacity: 0.4; }
.btn-stop { padding: 6px 12px; background: var(--red); color: #fff; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; font-family: var(--font); }
.bw-results { margin-top: 4px; }
.res-card { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.res-card.ok { border-left: 3px solid var(--green); }
.res-card.fail { border-left: 3px solid var(--red); }
.res-card h3 { font-size: 13px; margin-bottom: 10px; color: var(--fg); }
.res-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
.res-item { display: flex; flex-direction: column; gap: 2px; }
.rl { font-size: 9px; color: var(--fg3); text-transform: uppercase; letter-spacing: 1px; }
.rv { font-size: 14px; font-weight: 700; color: var(--fg); }
.err-msg { color: var(--red); font-size: 12px; }
.mono { font-family: var(--mono); }
.bw-history { margin-top: 8px; }
.bw-history h3 { font-size: 12px; color: var(--fg2); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.bw-history table { width: 100%; border-collapse: collapse; background: var(--bg2); border: 1px solid var(--border); border-radius: 3px; font-size: 11px; }
.bw-history th, .bw-history td { padding: 4px 8px; text-align: left; border-bottom: 1px solid var(--border); }
.bw-history th { color: var(--fg3); font-size: 9px; text-transform: uppercase; letter-spacing: 1px; }
</style>
