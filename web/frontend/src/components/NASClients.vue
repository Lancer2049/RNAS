<template>
  <div class="data-section">
    <h2>NAS Clients</h2>
    <p class="hint">RADIUS client devices authorized to send requests</p>
    <button class="btn-refresh" @click="load" :disabled="loading">{{ loading ? '...' : 'Refresh' }}</button>
    <table v-if="nas.length">
      <thead><tr><th>ID</th><th>NAS Name</th><th>Short Name</th><th>Type</th><th>Ports</th><th>Secret</th><th>Server</th></tr></thead>
      <tbody><tr v-for="n in nas" :key="n.id"><td class="mono">{{ n.id }}</td><td class="mono">{{ n.nasname }}</td><td>{{ n.shortname }}</td><td>{{ n.type }}</td><td>{{ n.ports }}</td><td class="mono">{{ n.secret }}</td><td>{{ n.server }}</td></tr></tbody>
    </table>
    <div v-else class="empty">No NAS clients found</div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const nas = ref([]); const loading = ref(false)
async function load() { loading=true; try{const r=await fetch('/api/aaa/nas');nas.value=(await r.json()).nas||[]}catch{};loading=false }
onMounted(load)
</script>
<style scoped>
.data-section { display:flex; flex-direction:column; gap:12px; }
.data-section h2 { font-size:15px; color:var(--fg); font-weight:600; } .hint { font-size:11px; color:var(--fg3); }
.btn-refresh { padding:5px 14px; background:var(--bg3); color:var(--accent); border:1px solid var(--accent); border-radius:3px; cursor:pointer; font-size:11px; font-family:var(--font); width:fit-content; }
.btn-refresh:hover { background:var(--accent); color:#000; }
table { width:100%; border-collapse:collapse; background:var(--bg2); border:1px solid var(--border); border-radius:3px; font-size:12px; }
th,td { padding:5px 10px; text-align:left; border-bottom:1px solid var(--border); } th { color:var(--fg3); font-weight:600; font-size:10px; text-transform:uppercase; letter-spacing:1px; background:var(--bg3); }
.mono { font-family:var(--mono); font-size:11px; } .empty { text-align:center; color:var(--fg3); padding:40px; font-size:12px; }
</style>
