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
.tunnel-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600;} .hint{font-size:11px;color:var(--fg3);}
.btn-refresh { align-self:flex-start; padding:5px 14px; background:var(--bg3); color:var(--accent); border:1px solid var(--accent); border-radius:3px; cursor:pointer; font-size:11px; font-family:var(--font); }
.btn-refresh:hover { background:var(--accent); color:#000; }
.tunnel-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:10px; }
.tunnel-card { background:var(--bg2); padding:14px; border-radius:3px; border:1px solid var(--border); border-left:3px solid var(--border); }
.tunnel-card.up { border-left-color:var(--green); }
.tunnel-header { display:flex; gap:8px; align-items:center; margin-bottom:6px; }
.tunnel-name { font-weight:600; font-size:14px; color:var(--fg); }
.tunnel-type { font-size:10px; background:var(--bg3); padding:2px 8px; border-radius:3px; color:var(--fg2); }
.tunnel-state { margin-left:auto; font-size:10px; padding:2px 8px; border-radius:3px; background:rgba(238,82,83,0.12); color:var(--red); font-weight:600; }
.tunnel-state.up { background:rgba(16,172,132,0.12); color:var(--green); }
.tunnel-detail { display:flex; flex-direction:column; gap:2px; font-size:11px; color:var(--fg2); }
.mono { font-family:var(--mono); color:var(--accent); }
.empty { text-align:center; color:var(--fg3); padding:40px; font-size:12px; }
</style>
