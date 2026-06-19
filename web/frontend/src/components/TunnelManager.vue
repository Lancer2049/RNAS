<template>
  <div class="tunnel-section">
    <h2>Tunnel Manager</h2>
    <p class="hint">GRE / IPIP / EoIP / VXLAN tunnel interfaces</p>
    <button class="btn-refresh" @click="fetchTunnels">🔄 Refresh</button>

    <div class="tunnel-grid">
      <div v-for="t in tunnels" :key="t.name" class="tunnel-card" :class="{up: t.up}">
        <div class="tunnel-header">
          <span class="tunnel-name">{{ t.name }}</span>
          <span class="tunnel-type">{{ t.type }}</span>
          <span class="tunnel-state" :class="{up: t.up}">{{ t.up ? 'UP' : 'DOWN' }}</span>
        </div>
        <div class="tunnel-detail" v-if="t.local">
          <span>{{ t.local }} ↔ {{ t.remote }}</span>
          <span v-if="t.inner_ip" class="mono">{{ t.inner_ip }}</span>
        </div>
      </div>
    </div>
    <div v-if="!tunnels.length" class="empty">No tunnels configured — use rnas-config generate gre/ipip/eoip/vxlan</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const tunnels = ref([])
async function fetchTunnels() {
  try {
    const r = await fetch('/api/tunnels')
    tunnels.value = (await r.json()).tunnels || []
  } catch {}
}
onMounted(fetchTunnels)
</script>

<style scoped>
.tunnel-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:18px;} .hint{font-size:13px;color:#888;}
.btn-refresh { align-self:flex-start; padding:6px 16px; background:#3b82f6; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px; }
.tunnel-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }
.tunnel-card { background:#fff; padding:14px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); border-left:3px solid #ddd; }
.tunnel-card.up { border-left-color:#22c55e; }
.tunnel-header { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
.tunnel-name { font-weight:600; font-size:14px; }
.tunnel-type { font-size:11px; background:#e2e8f0; padding:2px 8px; border-radius:4px; color:#64748b; }
.tunnel-state { margin-left:auto; font-size:11px; padding:2px 8px; border-radius:4px; background:#fef2f2; color:#dc2626; }
.tunnel-state.up { background:#dcfce7; color:#16a34a; }
.tunnel-detail { display:flex; flex-direction:column; gap:2px; font-size:12px; color:#666; }
.mono { font-family:monospace; color:#3b82f6; }
.empty { text-align:center; color:#999; padding:40px; }
</style>
