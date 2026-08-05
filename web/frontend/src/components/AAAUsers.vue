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
    <div v-else-if="error" class="empty err">{{ error }}</div>
    <div v-else class="empty">Loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const users = ref([])
const loading = ref(false)
const error = ref('')

async function loadUsers() {
  loading.value = true
  try {
    const res = await fetch('/api/aaa/users')
    const d = await res.json()
    users.value = d.users || []
    error.value = d.error || ''
  } catch { error.value = 'Failed to load users' }
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
.aaa-section { display: flex; flex-direction: column; gap: 14px; }
.aaa-section h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.hint { font-size: 11px; color: var(--fg3); }
.actions-bar { margin-bottom: 4px; }
.btn-refresh { padding: 5px 14px; background: var(--bg3); color: var(--accent); border: 1px solid var(--accent); border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.btn-refresh:hover { background: var(--accent); color: #000; }
table { width: 100%; border-collapse: collapse; background: var(--bg2); border: 1px solid var(--border); border-radius: 3px; }
th, td { padding: 5px 10px; text-align: left; border-bottom: 1px solid var(--border); font-size: 12px; }
th { color: var(--fg3); font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; background: var(--bg3); }
.mono { font-family: var(--mono); font-size: 11px; }
.empty { text-align: center; color: var(--fg3); padding: 40px; font-size: 12px; }
.btn-export { padding:5px 14px; background:var(--bg3); color:var(--fg2); border:1px solid var(--border); border-radius:3px; cursor:pointer; font-size:11px; font-family:var(--font); margin-left:6px }
</style>
