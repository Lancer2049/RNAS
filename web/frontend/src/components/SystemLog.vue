<template>
  <div class="log-view">
    <div class="log-toolbar">
      <select v-model="unit" @change="fetchLog">
        <option value="">All services</option>
        <option value="rnas-web.service">rnas-web</option>
        <option value="accel-ppp.service">accel-ppp</option>
        <option value="rnas-radius.service">rnas-radius</option>
        <option value="rnas-dhcp-relay.service">dhcp-relay</option>
        <option value="dnsmasq.service">dnsmasq</option>
        <option value="nftables.service">nftables</option>
        <option value="frr.service">FRRouting</option>
        <option value="prometheus.service">prometheus</option>
        <option value="sshd.service">sshd</option>
        <option value="NetworkManager.service">NetworkManager</option>
      </select>
      <select v-model="level" @change="fetchLog">
        <option value="">All levels</option>
        <option value="err">Errors only</option>
        <option value="warning">Warnings+</option>
        <option value="info">Info+</option>
      </select>
      <select v-model="lines" @change="fetchLog">
        <option :value="30">30</option><option :value="50">50</option><option :value="100">100</option><option :value="200">200</option>
      </select>
      <button class="btn" @click="fetchLog">Refresh</button>
      <label class="auto"><input type="checkbox" v-model="auto" /> Auto 5s</label>
    </div>
    <pre class="log-content">{{ log }}</pre>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
const log = ref(''), lines = ref(50), auto = ref(false), unit = ref(''), level = ref('')
let timer = null

async function fetchLog() {
  let url = `/api/system/log?lines=${lines.value}`
  if (unit.value) url += `&unit=${encodeURIComponent(unit.value)}`
  if (level.value) url += `&level=${encodeURIComponent(level.value)}`
  try { const r = await fetch(url); log.value = (await r.json()).log || '' } catch {}
}
watch(auto, v => { if (v) timer = setInterval(fetchLog, 5000); else clearInterval(timer) })
onMounted(fetchLog)
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.log-view { display: flex; flex-direction: column; gap: 8px; }
.log-toolbar { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.log-toolbar select, .log-toolbar .btn {
  padding: 4px 8px; background: var(--bg2); color: var(--fg);
  border: 1px solid var(--border); border-radius: 3px; font-size: 11px; font-family: var(--font);
}
.log-toolbar .btn { cursor: pointer; min-width: 60px; }
.log-toolbar .btn:hover { border-color: var(--accent); color: var(--accent); }
.log-toolbar select:focus { outline: none; border-color: var(--accent); }
.log-toolbar .auto { font-size: 11px; color: var(--fg2); display: flex; align-items: center; gap: 4px; cursor: pointer; }
.log-content {
  background: #0a0f14; color: #10ac84; font-family: var(--mono); font-size: 11px;
  padding: 12px; border: 1px solid var(--border); border-radius: 4px;
  white-space: pre-wrap; max-height: 55vh; overflow-y: auto; line-height: 1.6;
}
</style>
