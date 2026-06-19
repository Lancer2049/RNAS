<template>
  <div class="section">
    <h2>NetFlow / sFlow</h2>
    <p class="hint">softflowd traffic export to collector (VM2:2055)</p>
    <div class="stats-row">
      <div class="stat"><span class="label">Service</span><span class="value" :class="nf.running?'up':'down'">{{ nf.running ? 'Running' : 'Stopped' }}</span></div>
      <div class="stat"><span class="label">Collector</span><span class="value mono">{{ nf.collector || 'N/A' }}</span></div>
      <div class="stat"><span class="label">Interface</span><span class="value mono">{{ nf.interface || 'N/A' }}</span></div>
      <div class="stat"><span class="label">Format</span><span class="value">{{ nf.format || 'N/A' }}</span></div>
    </div>
    <h3>DHCP Relay</h3>
    <p class="hint">Relays DHCP requests to upstream RADIUS server</p>
    <div class="stats-row">
      <div class="stat"><span class="label">Service</span><span class="value" :class="dhcp.running?'up':'down'">{{ dhcp.running ? 'Running' : 'Stopped' }}</span></div>
      <div class="stat"><span class="label">Upstream</span><span class="value mono">{{ dhcp.upstream || 'N/A' }}</span></div>
      <div class="stat"><span class="label">GIADDR</span><span class="value mono">{{ dhcp.giaddr || 'N/A' }}</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const nf = ref({ running: false, collector: '', interface: '', format: '' })
const dhcp = ref({ running: false, upstream: '', giaddr: '' })
onMounted(async ()=>{
  try { const r=await fetch('/api/netflow'); nf.value=await r.json() } catch {}
  try { const r=await fetch('/api/dhcp-relay'); dhcp.value=await r.json() } catch {}
})
</script>

<style scoped>
.section { display:flex; flex-direction:column; gap:12px; } h2{font-size:18px;} h3{font-size:15px;margin:0;} .hint{font-size:13px;color:#888;}
.stats-row { display:flex; gap:16px; background:#fff; padding:12px 16px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); flex-wrap:wrap; }
.stat { display:flex; flex-direction:column; gap:4px; }
.label { font-size:11px; color:#888; text-transform:uppercase; }
.value { font-size:14px; font-weight:600; }
.value.up { color:#16a34a; } .value.down { color:#dc2626; } .mono { font-family:monospace; }
</style>
