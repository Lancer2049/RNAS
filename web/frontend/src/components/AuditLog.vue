<template>
  <div class="audit-page">
    <h2 class="page-title">Audit Log</h2>
    <p class="page-hint">Configuration changes and administrative actions — who did what and when</p>

    <div class="audit-actions">
      <select v-model="filter" class="filter-select" @change="load">
        <option value="">All actions</option>
        <option v-for="a in actionOptions" :key="a" :value="a">{{ a }}</option>
      </select>
      <button class="btn" @click="load">↻ Refresh</button>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
    </div>

    <table v-if="entries.length" class="audit-table">
      <thead><tr>
        <th>Time</th><th>User</th><th>Action</th><th>Target</th><th>Details</th><th>Result</th><th>IP</th>
      </tr></thead>
      <tbody>
        <tr v-for="e in entries" :key="e.id">
          <td class="mono">{{ fmtTime(e.timestamp) }}</td>
          <td class="mono">{{ e.username }}</td>
          <td><span class="act-badge" :class="actionClass(e.action)">{{ e.action }}</span></td>
          <td class="mono">{{ e.target || '—' }}</td>
          <td class="mono detail" :title="e.diff">{{ fmtDiff(e.diff) }}</td>
          <td><span class="result" :class="e.result === 'success' ? 'res-ok' : 'res-fail'">{{ e.result }}</span></td>
          <td class="mono muted">{{ e.ip_address || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No audit entries yet</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const entries = ref([])
const filter = ref('')
const msg = ref(''), msgType = ref('ok')
const actionOptions = ['config_update', 'config_apply', 'user_create', 'user_update', 'user_delete', 'cert_generate', 'cert_delete']

function fmtTime(ts) {
  if (!ts) return '—'
  return String(ts).replace('T', ' ').slice(0, 19)
}

function fmtDiff(diff) {
  if (!diff) return '—'
  try {
    const d = JSON.parse(diff)
    return Object.entries(d).slice(0, 3).map(([k, v]) => `${k}=${v}`).join(', ')
  } catch {
    return String(diff).slice(0, 60)
  }
}

function actionClass(action) {
  if (action === 'config_update' || action === 'config_apply') return 'act-config'
  if (action.startsWith('user')) return 'act-user'
  if (action.startsWith('cert')) return 'act-cert'
  return 'act-other'
}

async function load() {
  msg.value = ''
  try {
    const q = filter.value ? `?action=${encodeURIComponent(filter.value)}` : ''
    const r = await fetch(`/api/system/audit${q}`)
    entries.value = (await r.json()).entries || []
  } catch { msg.value = 'Load failed'; msgType.value = 'err' }
}

onMounted(load)
</script>

<style scoped>
.audit-page{display:flex;flex-direction:column;gap:12px}
.page-title{font-size:15px;color:var(--fg);font-weight:600}
.page-hint{font-size:11px;color:var(--fg3)}
.audit-actions{display:flex;gap:8px;align-items:center}
.filter-select{padding:4px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--font)}
.btn{padding:4px 12px;background:var(--bg3);color:var(--fg2);border:1px solid var(--border);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.audit-table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);font-size:11px}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap}
th{color:var(--fg3);font-size:9px;text-transform:uppercase;letter-spacing:1px;background:var(--bg3)}
.mono{font-family:var(--mono)}
.muted{color:var(--fg3)}
.detail{max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.act-badge{padding:2px 6px;border-radius:3px;font-size:10px;font-family:var(--mono)}
.act-config{color:var(--accent);background:rgba(255,200,0,.08)}
.act-user{color:#4fc3f7;background:rgba(79,195,247,.08)}
.act-cert{color:var(--green);background:rgba(0,200,80,.08)}
.act-other{color:var(--fg2);background:var(--bg3)}
.result{font-size:10px;font-family:var(--mono)}
.res-ok{color:var(--green)}
.res-fail{color:var(--red)}
.empty{text-align:center;color:var(--fg3);padding:24px}
.msg{font-size:11px;font-weight:500}.ok{color:var(--green)}.err{color:var(--red)}
</style>
