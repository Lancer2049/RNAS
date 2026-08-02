<template>
  <div class="snap-page snapshot-section">
    <h2>Config Snapshots</h2>
    <p class="hint">Point-in-time copies of /etc/rnas — create, diff, restore, delete</p>
    <div class="snap-actions">
      <input v-model="newName" class="name-input" placeholder="snapshot name (optional)" @keyup.enter="create" />
      <button class="btn btn-accent" @click="create" :disabled="creating">{{ creating ? '...' : '+ Create' }}</button>
      <button class="btn" @click="load">↻ Refresh</button>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
    </div>

    <table v-if="snaps.length">
      <thead><tr>
        <th>Name</th><th>Created</th><th>Files</th><th></th>
      </tr></thead>
      <tbody>
        <tr v-for="s in snaps" :key="s.name">
          <td class="mono">{{ s.name }}</td>
          <td>{{ fmtDate(s.created) }}</td>
          <td>{{ s.files }}</td>
          <td class="ops">
            <button class="btn btn-mini" @click="diff(s)" :disabled="diffing===s.name">{{ diffing===s.name ? '...' : 'Diff' }}</button>
            <button class="btn btn-mini" @click="restore(s)" :disabled="restoring===s.name">{{ restoring===s.name ? '...' : 'Restore' }}</button>
            <button class="btn btn-mini btn-del" @click="remove(s)" :disabled="deleting===s.name">{{ deleting===s.name ? '...' : 'Delete' }}</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No snapshots yet — create one to capture the current config</div>

    <div v-if="diffText !== null" class="diff-panel">
      <div class="diff-head">
        <span class="mono">{{ diffName }}</span>
        <span class="diff-status" :class="diffText === '(identical)' ? 'same' : 'differ'">
          {{ diffText === '(identical)' ? 'identical' : 'differs from live config' }}
        </span>
        <button class="btn btn-mini" @click="diffText=null">✕ Close</button>
      </div>
      <pre class="diff-body">{{ diffText }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const snaps = ref([]), newName = ref('')
const msg = ref(''), msgType = ref('ok')
const creating = ref(false), restoring = ref(''), deleting = ref(''), diffing = ref('')
const diffText = ref(null), diffName = ref('')

function fmtDate(t) { return new Date(t * 1000).toLocaleString() }

async function load() {
  msg.value = ''
  try {
    const r = await fetch('/api/config/snapshots')
    snaps.value = (await r.json()).snapshots || []
  } catch { msg.value = 'Load failed'; msgType.value = 'err' }
}

async function create() {
  creating.value = true
  try {
    const r = await fetch('/api/config/snapshot', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.value.trim() })
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Create failed: ' + (d.detail || r.status); msgType.value = 'err' }
    else { newName.value = ''; await load(); msg.value = `Snapshot created (${d.files} files)`; msgType.value = 'ok' }
  } catch (e) { msg.value = 'Create error: ' + e.message; msgType.value = 'err' }
  creating.value = false
}

async function diff(s) {
  diffing.value = s.name
  try {
    const r = await fetch(`/api/config/snapshot/${encodeURIComponent(s.name)}/diff`)
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Diff failed: ' + (d.detail || r.status); msgType.value = 'err' }
    else { diffName.value = s.name; diffText.value = d.diff || '(empty)'; msg.value = '' }
  } catch (e) { msg.value = 'Diff error: ' + e.message; msgType.value = 'err' }
  diffing.value = ''
}

async function restore(s) {
  if (!confirm(`Restore config from "${s.name}"? Current config will be backed up first.`)) return
  restoring.value = s.name
  try {
    const r = await fetch(`/api/config/snapshot/${encodeURIComponent(s.name)}/restore`, { method: 'POST' })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Restore failed: ' + (d.detail || r.status); msgType.value = 'err' }
    else { msg.value = `Restored from "${s.name}" (backup: ${d.backup})`; msgType.value = 'ok' }
  } catch (e) { msg.value = 'Restore error: ' + e.message; msgType.value = 'err' }
  restoring.value = ''
}

async function remove(s) {
  if (!confirm(`Delete snapshot "${s.name}"?`)) return
  deleting.value = s.name
  try {
    const r = await fetch(`/api/config/snapshot/${encodeURIComponent(s.name)}`, { method: 'DELETE' })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Delete failed: ' + (d.detail || r.status); msgType.value = 'err' }
    else { await load(); msg.value = 'Deleted'; msgType.value = 'ok' }
  } catch (e) { msg.value = 'Delete error: ' + e.message; msgType.value = 'err' }
  deleting.value = ''
}

onMounted(load)
</script>

<style scoped>
.snap-page{display:flex;flex-direction:column;gap:12px}
h2{font-size:15px;color:var(--fg);font-weight:600}
.hint{font-size:11px;color:var(--fg3)}
.snap-actions{display:flex;gap:8px;align-items:center}
.name-input{padding:5px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--mono);width:220px;outline:none}
.name-input:focus{border-color:var(--accent)}
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);font-size:11px}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--fg3);font-size:9px;text-transform:uppercase;letter-spacing:1px;background:var(--bg3)}
.mono{font-family:var(--mono)}
.ops{display:flex;gap:4px;justify-content:flex-end}
.empty{text-align:center;color:var(--fg3);padding:24px}
.btn{padding:4px 12px;background:var(--bg3);color:var(--fg2);border:1px solid var(--border);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.btn-accent{background:var(--accent);color:#000;border-color:var(--accent)}
.btn-mini{padding:2px 8px;font-size:10px}
.btn-del{color:var(--red);border-color:rgba(255,0,0,.3)}
.btn:disabled{opacity:.4}
.msg{font-size:11px;font-weight:500}.ok{color:var(--green)}.err{color:var(--red)}
.diff-panel{margin-top:6px;background:var(--bg2);border:1px solid var(--border);border-radius:3px}
.diff-head{display:flex;gap:10px;align-items:center;padding:6px 10px;border-bottom:1px solid var(--border);font-size:11px}
.diff-status{font-size:10px;padding:1px 8px;border-radius:3px}
.diff-status.same{color:var(--green);background:rgba(0,200,80,.08)}
.diff-status.differ{color:var(--red);background:rgba(255,0,0,.08)}
.diff-body{margin:0;padding:10px;font-size:10px;font-family:var(--mono);max-height:300px;overflow:auto;color:var(--fg2);white-space:pre-wrap}
</style>
