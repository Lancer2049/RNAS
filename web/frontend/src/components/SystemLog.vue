<template>
  <div class="log-view">
    <div class="log-toolbar">
      <select v-model="lines" @change="fetchLog">
        <option :value="30">30 lines</option><option :value="50">50</option><option :value="100">100</option><option :value="200">200</option>
      </select>
      <button class="btn" @click="fetchLog">Refresh</button>
      <label class="auto"><input type="checkbox" v-model="auto" /> Auto (5s)</label>
    </div>
    <pre class="log-content">{{ log }}</pre>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
const log = ref(''), lines = ref(50), auto = ref(false)
let timer = null

async function fetchLog() {
  try { const r=await fetch(`/api/system/log?lines=${lines.value}`); log.value=(await r.json()).log||'' } catch {}
}
watch(auto, v => { if(v) timer=setInterval(fetchLog,5000); else clearInterval(timer) })
onMounted(fetchLog)
onUnmounted(()=>clearInterval(timer))
</script>

<style scoped>
.log-view { display:flex; flex-direction:column; gap:8px; }
.log-toolbar { display:flex; gap:8px; align-items:center; }
.log-toolbar select, .log-toolbar .btn { padding:4px 10px; }
.log-toolbar .auto { font-size:11px; color:var(--fg2); display:flex; align-items:center; gap:4px; }
.log-content { background:#0a0f14; color:#10ac84; font-family:var(--mono); font-size:11px; padding:12px; border:1px solid var(--border); border-radius:4px; white-space:pre-wrap; max-height:500px; overflow-y:auto; line-height:1.6; }
</style>
