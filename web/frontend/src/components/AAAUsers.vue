<template>
  <div class="aaa-section">
    <h2>RADIUS Users</h2>
    <p class="hint">Users configured in FreeRADIUS database (radcheck table)</p>

    <div class="actions-bar">
      <button class="btn-refresh" @click="loadUsers" :disabled="loading">{{ loading ? 'Loading...' : 'Refresh' }}</button>
    <button class="btn-export" @click="exportCSV" v-if="users.length">📥 CSV</button>
    </div>

    <table v-if="users.length">
      <thead>
        <tr><th>Username</th><th>Attribute</th><th>Value</th></tr>
      </thead>
      <tbody>
        <tr v-for="(u, i) in users" :key="i">
          <td class="mono">{{ u.username }}</td>
          <td>{{ u.attribute }}</td>
          <td class="mono">{{ u.value }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">Loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const users = ref([])
const loading = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const res = await fetch('/api/aaa/users')
    const d = await res.json()
    users.value = d.users || []
  } catch {}
  loading.value = false
}
function exportCSV() {
  const hdr = 'Username,Attribute,Value\n'
  const rows = users.value.map(u => [u.username,u.attribute,u.value].join(',')).join('\n')
  const blob = new Blob([hdr+rows],{type:'text/csv'})
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='radcheck.csv'; a.click()
}
onMounted(loadUsers)
</script>

<style scoped>
.aaa-section { display: flex; flex-direction: column; gap: 16px; }
.aaa-section h2 { font-size: 18px; }
.hint { font-size: 13px; color: #888; }
.actions-bar { margin-bottom: 8px; }
.btn-refresh { padding: 6px 16px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { color: #666; font-weight: 600; font-size: 11px; text-transform: uppercase; background: #f8f9fa; }
.mono { font-family: monospace; font-size: 12px; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
