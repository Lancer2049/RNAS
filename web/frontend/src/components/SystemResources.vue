<template>
  <div class="sys-res" v-if="data">
    <h3 class="sec-title">System Resources</h3>
    <div class="res-grid">
      <!-- Memory -->
      <div class="res-item">
        <span class="res-label">Memory</span>
        <div class="res-bar"><div class="res-fill mem" :style="{width: memPct+'%'}"></div></div>
        <span class="res-val">{{ data.memory || '--' }}</span>
      </div>
      <!-- Disk -->
      <div class="res-item">
        <span class="res-label">Disk</span>
        <div class="res-bar"><div class="res-fill disk" :style="{width: diskPct+'%'}"></div></div>
        <span class="res-val">{{ data.disk || '--' }}</span>
      </div>
      <!-- Load -->
      <div class="res-item">
        <span class="res-label">Load Average</span>
        <div class="res-bar"><div class="res-fill load" :style="{width: loadPct+'%'}"></div></div>
        <span class="res-val mono">{{ data.load || '--' }}</span>
      </div>
      <!-- CPU Count -->
      <div class="res-item">
        <span class="res-label">CPU Cores</span>
        <span class="res-val mono">{{ data.cpu_cores || '--' }}</span>
      </div>
      <!-- OS -->
      <div class="res-item">
        <span class="res-label">OS</span>
        <span class="res-val mono">{{ data.os || '--' }}</span>
      </div>
      <!-- Kernel -->
      <div class="res-item">
        <span class="res-label">Kernel</span>
        <span class="res-val mono">{{ data.kernel || '--' }}</span>
      </div>
      <!-- Architecture -->
      <div class="res-item">
        <span class="res-label">Architecture</span>
        <span class="res-val mono">{{ data.arch || '--' }}</span>
      </div>
      <!-- Uptime -->
      <div class="res-item">
        <span class="res-label">Uptime</span>
        <span class="res-val mono">{{ data.uptime || '--' }}</span>
      </div>
      <!-- Boot Time -->
      <div class="res-item">
        <span class="res-label">Boot Time</span>
        <span class="res-val mono">{{ data.boot_time || '--' }}</span>
      </div>
      <!-- Hostname -->
      <div class="res-item">
        <span class="res-label">Hostname</span>
        <span class="res-val mono">{{ data.hostname || '--' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
const data = ref(null)

const memPct = computed(() => {
  if (!data.value?.memory) return 0
  const p = data.value.memory.split('/')
  return p.length > 1 ? (parseFloat(p[0].replace(/[^0-9.]/g,'')) / parseFloat(p[1].replace(/[^0-9.]/g,'')) * 100) : 0
})
const diskPct = computed(() => {
  if (!data.value?.disk) return 0
  const p = data.value.disk.split('/')
  return p.length > 1 ? parseFloat(p[0].replace(/[^0-9.]/g,'')) : 0
})
const loadPct = computed(() => {
  if (!data.value?.load) return 0
  const v = parseFloat(data.value.load.split(/\s+/)[0])
  return Math.min(isNaN(v) ? 0 : v * 25, 100)
})

async function load() {
  try { const r = await fetch('/api/system/status'); data.value = await r.json() } catch {}
}
onMounted(load)
</script>

<style scoped>
.sys-res { background: var(--bg2); border: 1px solid var(--border); padding: 12px 14px; border-radius: 3px; margin-bottom: 12px; }
.sec-title { font-size: 12px; text-transform: uppercase; color: var(--fg2); letter-spacing: 1px; margin-bottom: 10px; }
.res-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px 16px; }
.res-item { display: flex; flex-direction: column; gap: 3px; }
.res-label { font-size: 9px; color: var(--fg3); text-transform: uppercase; letter-spacing: 1px; }
.res-bar { height: 5px; background: var(--bg3); border-radius: 2px; overflow: hidden; margin: 2px 0; min-width: 60px; }
.res-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
.res-fill.mem { background: var(--accent); }
.res-fill.disk { background: var(--green); }
.res-fill.load { background: var(--red); opacity: 0.7; }
.res-val { font-size: 13px; font-weight: 700; color: var(--fg); font-family: var(--font); }
.mono { font-family: var(--mono); }
</style>
