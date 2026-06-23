<template>
  <div class="terminal-page">
    <h2>Web Terminal</h2>
    <p class="hint">Shell access to RNAS server — commands run as root</p>
    <div ref="terminalContainer" class="terminal-wrap"></div>
    <div class="term-toolbar">
      <button class="btn" @click="connect">Connect</button>
      <button class="btn" @click="disconnect" :disabled="!ws">Disconnect</button>
      <button class="btn" @click="clear">Clear</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from '@xterm/addon-fit'
import 'xterm/css/xterm.css'

const terminalContainer = ref(null)
let term = null
let fitAddon = null
let ws = null
const WS_URL = `ws://${location.host}/api/terminal`

function connect() {
  if (ws) return
  try {
    ws = new WebSocket(WS_URL)
    ws.onopen = () => { term.focus() }
    ws.onmessage = e => { term.write(e.data) }
    ws.onclose = () => { ws = null; term.writeln('\\r\\n[Disconnected]') }
    ws.onerror = () => { ws?.close() }
  } catch {}
}

function disconnect() {
  if (ws) { ws.send('__CLOSE__'); ws.close(); ws = null }
}

function clear() { term.clear() }

onMounted(() => {
  term = new Terminal({ cursorBlink: true, fontSize: 13, fontFamily: 'var(--mono, monospace)', theme: { background: '#0a0f14', foreground: '#10ac84', cursor: '#0abde3' } })
  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalContainer.value)
  fitAddon.fit()
  term.onData(data => { if (ws && ws.readyState === WebSocket.OPEN) ws.send(data) })
  term.writeln('Click "Connect" to start terminal session')
  setTimeout(() => fitAddon.fit(), 100)
})

onUnmounted(() => { disconnect(); term?.dispose() })
</script>

<style scoped>
.terminal-page{display:flex;flex-direction:column;gap:8px}
h2{font-size:15px;color:var(--fg);font-weight:600}
.hint{font-size:11px;color:var(--fg3)}
.terminal-wrap{height:60vh;border:1px solid var(--border);border-radius:3px;overflow:hidden}
.term-toolbar{display:flex;gap:8px}
</style>
