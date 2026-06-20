<template>
  <div class="health-section" v-if="data">
    <h3>System Health</h3>
    <div class="health-grid">
      <div class="health-item" v-for="s in data" :key="s.name">
        <span class="dot" :class="s.active==='active'?'up':'down'"></span>
        <span class="name">{{ s.name }}</span>
        <span class="state">{{ s.active==='active'?'UP':'DOWN' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const data = ref(null)
async function load() {
  try { const r = await fetch('/api/system/status'); data.value = (await r.json()).services } catch {}
}
onMounted(() => { load(); setInterval(load, 10000) })
</script>

<style scoped>
.health-section{background:var(--bg2);padding:12px 14px;border:1px solid var(--border);border-radius:3px;margin-bottom:14px}
.health-section h3{font-size:12px;color:var(--fg2);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}
.health-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:4px}
.health-item{display:flex;align-items:center;gap:8px;font-size:11px;padding:4px 0}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}.dot.up{background:var(--green)}.dot.down{background:var(--red)}
.name{color:var(--fg3);flex:1}.state{font-weight:600;font-size:10px;color:var(--green)}
.health-item:has(.down) .state{color:var(--red)}
</style>
