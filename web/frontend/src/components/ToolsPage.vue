<template>
  <div class="tools-section">
    <h2>Diagnostics</h2>

    <div class="card">
      <h3>Ping</h3>
      <div class="tool-row">
        <input v-model="pingHost" placeholder="192.168.0.1" @keyup.enter="runPing" />
        <button @click="runPing" :disabled="pingRunning">{{ pingRunning ? '...' : 'Ping' }}</button>
      </div>
      <pre v-if="pingOutput" class="output">{{ pingOutput }}</pre>
    </div>

    <div class="card">
      <h3>Traceroute</h3>
      <div class="tool-row">
        <input v-model="traceHost" placeholder="192.168.0.202" @keyup.enter="runTrace" />
        <button @click="runTrace" :disabled="traceRunning">{{ traceRunning ? '...' : 'Trace' }}</button>
      </div>
      <pre v-if="traceOutput" class="output">{{ traceOutput }}</pre>
    </div>

    <div class="card">
      <h3>RADIUS Test</h3>
      <div class="tool-row">
        <input v-model="radUser" placeholder="testuser" />
        <input v-model="radPass" placeholder="testpass" type="password" />
        <button @click="runRadiusTest" :disabled="radRunning">{{ radRunning ? '...' : 'Auth Test' }}</button>
      </div>
      <pre v-if="radOutput" class="output">{{ radOutput }}</pre>
    </div>

    <div class="card">
      <h3>CoA / Disconnect</h3>
      <div class="tool-row">
        <input v-model="coaUser" placeholder="username" />
        <button @click="runCoa" :disabled="coaRunning">{{ coaRunning ? '...' : 'Disconnect' }}</button>
      </div>
      <pre v-if="coaOutput" class="output">{{ coaOutput }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const pingHost = ref('192.168.0.202')
const pingOutput = ref('')
const pingRunning = ref(false)

const traceHost = ref('192.168.0.202')
const traceOutput = ref('')
const traceRunning = ref(false)

const radUser = ref('testuser')
const radPass = ref('testpass')
const radOutput = ref('')
const radRunning = ref(false)

const coaUser = ref('')
const coaOutput = ref('')
const coaRunning = ref(false)

async function runPing() {
  pingRunning.value = true; pingOutput.value = '';
  try {
    const res = await fetch(`/api/tools/ping?host=${encodeURIComponent(pingHost.value)}`)
    pingOutput.value = (await res.json()).output || 'No response'
  } catch(e) { pingOutput.value = 'Error: ' + e.message }
  pingRunning.value = false
}

async function runTrace() {
  traceRunning.value = true; traceOutput.value = '';
  try {
    const res = await fetch(`/api/tools/trace?host=${encodeURIComponent(traceHost.value)}`)
    traceOutput.value = (await res.json()).output || 'No response'
  } catch(e) { traceOutput.value = 'Error: ' + e.message }
  traceRunning.value = false
}

async function runRadiusTest() {
  radRunning.value = true; radOutput.value = '';
  try {
    const res = await fetch(`/api/tools/radius-test?user=${encodeURIComponent(radUser.value)}&pass=${encodeURIComponent(radPass.value)}`)
    radOutput.value = (await res.json()).output || 'No response'
  } catch(e) { radOutput.value = 'Error: ' + e.message }
  radRunning.value = false
}

async function runCoa() {
  if (!coaUser.value) return
  coaRunning.value = true; coaOutput.value = '';
  try {
    const res = await fetch(`/api/tools/coa?user=${encodeURIComponent(coaUser.value)}`, { method: 'POST' })
    coaOutput.value = (await res.json()).output || 'No response'
  } catch(e) { coaOutput.value = 'Error: ' + e.message }
  coaRunning.value = false
}
</script>

<style scoped>
.tools-section { display: flex; flex-direction: column; gap: 14px; }
.tools-section h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.card { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.card h3 { font-size: 12px; margin-bottom: 8px; color: var(--fg2); text-transform: uppercase; letter-spacing: 1px; }
.tool-row { display: flex; gap: 8px; margin-bottom: 8px; }
.tool-row input { flex: 1; padding: 5px 10px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; }
.tool-row input:focus { border-color: var(--accent); }
.tool-row button { padding: 5px 14px; background: var(--bg3); color: var(--accent); border: 1px solid var(--accent); border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.tool-row button:hover { background: var(--accent); color: #000; }
.tool-row button:disabled { opacity: 0.4; }
.output { background: #0a0f14; color: var(--green); padding: 12px; border-radius: 3px; font-family: var(--mono); font-size: 11px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; border: 1px solid var(--border); }
</style>
