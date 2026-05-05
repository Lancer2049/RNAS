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
.data-section h2 { font-size:18px; } .hint { font-size:13px; color:#888; }
.btn-refresh { padding:6px 16px; background:#3b82f6; color:#fff; border:none; border-radius:4px; cursor:pointer; font-size:13px; width:fit-content; }
table { width:100%; border-collapse:collapse; background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); font-size:13px; }
th,td { padding:8px 12px; text-align:left; border-bottom:1px solid #eee; } th { color:#666; font-weight:600; font-size:11px; text-transform:uppercase; background:#f8f9fa; }
.mono { font-family:monospace; font-size:12px; } .empty { text-align:center; color:#999; padding:40px; }
</style>
