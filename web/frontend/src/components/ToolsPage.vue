<template>
  <div class="tools-section">
    <h2>Diagnostics</h2>
    <div class="diag-tabs">
      <button :class="{sel: dt==='ping'}" @click="dt='ping'">Ping</button>
      <button :class="{sel: dt==='trace'}" @click="dt='trace'">Traceroute</button>
      <button :class="{sel: dt==='dns'}" @click="dt='dns'">DNS</button>
      <button :class="{sel: dt==='radius'}" @click="dt='radius'">RADIUS</button>
      <button :class="{sel: dt==='coa'}" @click="dt='coa'">CoA</button>
      <button :class="{sel: dt==='bw'}" @click="dt='bw'">BW Test</button>
      <button :class="{sel: dt==='cap'}" @click="dt='cap'">Capture</button>
    </div>

    <!-- Ping -->
    <div v-if="dt==='ping'" class="card">
      <h3>Ping</h3>
      <div class="tool-row"><input v-model="pingHost" @keyup.enter="runPing" /><button @click="runPing" :disabled="pingRunning">{{ pingRunning ? '...' : 'Ping' }}</button></div>
      <pre v-if="pingOutput" class="output">{{ pingOutput }}</pre>
    </div>

    <!-- Traceroute -->
    <div v-if="dt==='trace'" class="card">
      <h3>Traceroute</h3>
      <div class="tool-row"><input v-model="traceHost" @keyup.enter="runTrace" /><button @click="runTrace" :disabled="traceRunning">{{ traceRunning ? '...' : 'Trace' }}</button></div>
      <pre v-if="traceOutput" class="output">{{ traceOutput }}</pre>
    </div>

    <!-- DNS Lookup -->
    <div v-if="dt==='dns'" class="card">
      <h3>DNS Lookup</h3>
      <div class="tool-row">
        <input v-model="dnsHost" placeholder="example.com" @keyup.enter="runDns" />
        <select v-model="dnsType"><option value="a">A</option><option value="aaaa">AAAA</option><option value="mx">MX</option><option value="ns">NS</option></select>
        <button @click="runDns" :disabled="dnsRunning">{{ dnsRunning ? '...' : 'Lookup' }}</button>
      </div>
      <pre v-if="dnsOutput" class="output">{{ dnsOutput }}</pre>
    </div>

    <!-- RADIUS Test -->
    <div v-if="dt==='radius'" class="card">
      <h3>RADIUS Test</h3>
      <div class="tool-row"><input v-model="radUser" placeholder="username" /><input v-model="radPass" type="password" placeholder="password" /><button @click="runRadiusTest" :disabled="radRunning">{{ radRunning ? '...' : 'Auth Test' }}</button></div>
      <pre v-if="radOutput" class="output">{{ radOutput }}</pre>
    </div>

    <!-- CoA -->
    <div v-if="dt==='coa'" class="card">
      <h3>CoA Disconnect</h3>
      <div class="tool-row"><input v-model="coaUser" placeholder="username" /><button @click="runCoa" :disabled="coaRunning">{{ coaRunning ? '...' : 'Disconnect' }}</button></div>
      <pre v-if="coaOutput" class="output">{{ coaOutput }}</pre>
    </div>

    <!-- Bandwidth Test -->
    <div v-if="dt==='bw'" class="card">
      <h3>Bandwidth Test</h3>
      <div class="tool-row">
        <input v-model="bwTarget" placeholder="target IP" />
        <input v-model.number="bwPort" type="number" placeholder="port" style="width:80px" />
        <select v-model="bwProto"><option value="tcp">TCP</option><option value="udp">UDP</option></select>
        <select v-model="bwDuration" style="width:70px"><option :value="3">3s</option><option :value="5">5s</option><option :value="10">10s</option></select>
        <button @click="runBw" :disabled="bwRunning">{{ bwRunning ? '...' : 'Test' }}</button>
      </div>
      <pre v-if="bwOutput" class="output">{{ bwOutput }}</pre>
    </div>

    <!-- Packet Capture -->
    <div v-if="dt==='cap'" class="card">
      <h3>Packet Capture</h3>
      <div class="tool-row">
        <input v-model="capIface" placeholder="interface" style="width:80px" />
        <input v-model.number="capPort" type="number" placeholder="port" style="width:70px" />
        <input v-model.number="capCount" type="number" placeholder="packets" style="width:70px" />
        <button @click="capStart" :disabled="capRunning">Start</button>
        <button @click="capStop" :disabled="!capRunning">Stop</button>
        <button @click="capStatus">Status</button>
      </div>
      <div v-if="capMsg" class="output">{{ capMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const dt = ref('ping')
const pingHost = ref('192.168.0.1'), pingOutput = ref(''), pingRunning = ref(false)
const traceHost = ref('192.168.0.202'), traceOutput = ref(''), traceRunning = ref(false)
const dnsHost = ref('google.com'), dnsType = ref('a'), dnsOutput = ref(''), dnsRunning = ref(false)
const radUser = ref('testuser'), radPass = ref('testpass'), radOutput = ref(''), radRunning = ref(false)
const coaUser = ref(''), coaOutput = ref(''), coaRunning = ref(false)
const bwTarget = ref('192.168.0.203'), bwPort = ref(5201), bwProto = ref('tcp'), bwDuration = ref(5), bwOutput = ref(''), bwRunning = ref(false)
const capIface = ref('ens33'), capPort = ref(1812), capCount = ref(100), capRunning = ref(false), capMsg = ref('')

async function runPing() {
  pingRunning.value = true; pingOutput.value = ''
  try { const r = await fetch(`/api/tools/ping?host=${encodeURIComponent(pingHost.value)}`); pingOutput.value = (await r.json()).output || 'No response' } catch(e) { pingOutput.value = 'Error: ' + e.message }
  pingRunning.value = false
}
async function runTrace() {
  traceRunning.value = true; traceOutput.value = ''
  try { const r = await fetch(`/api/tools/trace?host=${encodeURIComponent(traceHost.value)}`); traceOutput.value = (await r.json()).output || 'No response' } catch(e) { traceOutput.value = 'Error: ' + e.message }
  traceRunning.value = false
}
async function runDns() {
  dnsRunning.value = true; dnsOutput.value = ''
  try { const r = await fetch(`/api/tools/dns?host=${encodeURIComponent(dnsHost.value)}&type=${dnsType.value}`); dnsOutput.value = (await r.json()).output || 'No response' } catch(e) { dnsOutput.value = 'Error: ' + e.message }
  dnsRunning.value = false
}
async function runRadiusTest() {
  radRunning.value = true; radOutput.value = ''
  try { const r = await fetch(`/api/tools/radius-test?user=${encodeURIComponent(radUser.value)}&pass=${encodeURIComponent(radPass.value)}`); radOutput.value = (await r.json()).output || '' } catch(e) { radOutput.value = 'Error: ' + e.message }
  radRunning.value = false
}
async function runCoa() {
  if (!coaUser.value) return; coaRunning.value = true; coaOutput.value = ''
  try { const r = await fetch(`/api/tools/coa?user=${encodeURIComponent(coaUser.value)}`); coaOutput.value = (await r.json()).output || 'No response' } catch(e) { coaOutput.value = 'Error: ' + e.message }
  coaRunning.value = false
}
async function runBw() {
  bwRunning.value = true; bwOutput.value = ''
  try {
    const r = await fetch('/api/bandwidth-test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: bwTarget.value, port: bwPort.value, duration: bwDuration.value, proto: bwProto.value }) })
    const d = await r.json()
    bwOutput.value = d.ok ? `TX: ${d.sent_mbps} Mbps\nRX: ${d.recv_mbps} Mbps\nRetrans: ${d.retransmits}` : `Error: ${d.error || 'unknown'}`
  } catch(e) { bwOutput.value = 'Error: ' + e.message }
  bwRunning.value = false
}
async function capStart() {
  capRunning.value = true; capMsg.value = ''
  try { const r = await fetch('/api/tools/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'start', interface: capIface.value, port: capPort.value, count: capCount.value }) }); const d = await r.json(); capMsg.value = d.status + ' (pid ' + d.pid + ')' } catch(e) { capMsg.value = 'Error: ' + e.message; capRunning.value = false }
}
async function capStop() {
  try { const r = await fetch('/api/tools/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'stop' }) }); const d = await r.json(); capMsg.value = d.status; capRunning.value = false } catch(e) { capMsg.value = 'Error: ' + e.message }
}
async function capStatus() {
  try { const r = await fetch('/api/tools/capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'status' }) }); const d = await r.json(); capMsg.value = d.running ? 'Running' : 'Stopped'; capRunning.value = d.running } catch(e) { capMsg.value = 'Error: ' + e.message }
}
</script>

<style scoped>
.tools-section { display:flex; flex-direction:column; gap:12px; }
h2{font-size:15px;color:var(--fg);font-weight:600}
.diag-tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:4px}
.diag-tabs button{padding:5px 14px;border:1px solid var(--border);border-radius:3px;background:var(--bg);color:var(--fg2);cursor:pointer;font-size:11px;font-family:var(--font)}
.diag-tabs button.sel{background:var(--accent);color:#000;border-color:var(--accent)}
.card{background:var(--bg2);padding:12px;border:1px solid var(--border);border-radius:3px}
.card h3{font-size:11px;margin-bottom:8px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px}
.tool-row{display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap}
.tool-row input,.tool-row select{padding:5px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--mono);outline:none;flex:1;min-width:80px}
.tool-row input:focus,.tool-row select:focus{border-color:var(--accent)}
.tool-row button{padding:5px 14px;background:var(--bg3);color:var(--accent);border:1px solid var(--accent);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.tool-row button:hover{background:var(--accent);color:#000}
.tool-row button:disabled{opacity:0.4}
.output{background:#0a0f14;color:var(--green);padding:10px;border-radius:3px;font-family:var(--mono);font-size:10px;white-space:pre-wrap;max-height:300px;overflow-y:auto;border:1px solid var(--border);margin-top:4px}
</style>
