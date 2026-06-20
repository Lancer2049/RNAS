<template>
  <div class="tool-section">
    <h2>Packet Sniffer</h2>
    <p class="hint">Capture RADIUS/PPP traffic for analysis (tcpdump :1812/1813/3799)</p>
    <div class="controls">
      <button @click="start" :disabled="running" class="btn-start">▶ Start Capture</button>
      <button @click="stop" :disabled="!running" class="btn-stop">⏹ Stop</button>
      <span v-if="running" class="status running">● Capturing... ({{ formatSize(size) }})</span>
      <span v-else class="status stopped">○ Stopped</span>
    </div>
    <p class="path" v-if="size>0">File: /tmp/rnas-sniffer.pcap ({{ formatSize(size) }})</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const running=ref(false), size=ref(0)
async function check(){try{const r=await fetch('/api/sniffer/status');const d=await r.json();running.value=d.running;size.value=d.size}catch{}}
async function start(){await fetch('/api/sniffer/start');check()}
async function stop(){await fetch('/api/sniffer/stop');check()}
function formatSize(n){if(!n)return'0B';if(n<1024)return n+'B';return (n/1024).toFixed(1)+'KB'}
onMounted(check)
</script>
<style scoped>
.tool-section{display:flex;flex-direction:column;gap:12px} h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.controls{display:flex;gap:12px;align-items:center;background:var(--bg2);padding:14px;border:1px solid var(--border);border-radius:3px}
.btn-start{padding:6px 16px;background:var(--green);color:#000;border:none;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--font)}
.btn-stop{padding:6px 16px;background:var(--red);color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--font)}
button:disabled{opacity:.4}
.status{font-size:13px;font-weight:600} .running{color:var(--green)} .stopped{color:var(--fg3)}
.path{font-family:var(--mono);font-size:11px;color:var(--fg2)}
</style>
