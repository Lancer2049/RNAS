<template>
  <div class="cert-page">
    <h2>Certificate Manager</h2>
    <p class="hint">SSL/TLS certificates for SSTP, HTTPS, OpenVPN, 802.1X</p>
    <div class="cert-actions">
      <button class="btn" @click="showGen=true">+ Generate Self-Signed</button>
      <button class="btn" @click="load">↻ Refresh</button>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
    </div>

    <div v-if="showGen" class="gen-form">
      <input v-model="genName" placeholder="Name (e.g. server)" />
      <input v-model="genCN" placeholder="Common Name (e.g. RNAS Server)" />
      <input v-model.number="genDays" type="number" placeholder="Days" />
      <button class="btn btn-accent" @click="generate">Generate</button>
      <button class="btn" @click="showGen=false">Cancel</button>
    </div>

    <table v-if="certs.length">
      <thead><tr>
        <th>Name</th><th>Type</th><th>Subject</th><th>Expires</th><th>Size</th><th>Modified</th><th>Usage</th><th></th>
      </tr></thead>
      <tbody>
        <tr v-for="c in certs" :key="c.name">
          <td class="mono">{{ c.name }}</td>
          <td>{{ c.kind }}</td>
          <td class="mono">{{ c.subject || '—' }}</td>
          <td>
            <span v-if="c.expires" class="exp-badge" :class="expClass(c.days_left)">
              {{ new Date(c.expires*1000).toLocaleDateString() }}
              <span v-if="c.days_left !== null" class="days">({{ c.days_left }}d)</span>
            </span>
            <span v-else class="muted">—</span>
          </td>
          <td>{{ (c.size/1024).toFixed(1) }}KB</td>
          <td>{{ new Date(c.modified*1000).toLocaleDateString() }}</td>
          <td><span v-if="c.usage && c.usage.length" class="usage" :title="c.usage.join(', ')">{{ c.usage.length }} ref(s)</span><span v-else class="muted">unused</span></td>
          <td><button class="btn btn-del" :disabled="deleting===c.name" @click="remove(c)">{{ deleting===c.name ? '...' : 'Delete' }}</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No certificates found</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const certs = ref([]), showGen = ref(false)
const genName = ref('server'), genCN = ref('RNAS Server'), genDays = ref(3650)
const msg = ref(''), msgType = ref('ok'), deleting = ref('')

function expClass(days) {
  if (days === null) return 'exp-unknown'
  if (days < 0) return 'exp-expired'
  if (days < 30) return 'exp-warn'
  if (days < 90) return 'exp-soon'
  return 'exp-ok'
}

async function load() {
  msg.value = ''
  try {
    const r = await fetch('/api/system/certificates')
    certs.value = (await r.json()).certificates || []
  } catch { msg.value = 'Load failed'; msgType.value = 'err' }
}

async function generate() {
  if (!genName.value.trim() || !genDays.value || genDays.value < 1) { msg.value = 'Name and days (>=1) are required'; msgType.value = 'err'; return }
  try {
    const r = await fetch('/api/system/certificates/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: genName.value.trim(), cn: genCN.value, days: genDays.value }) })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Generate failed: ' + (d.detail || r.status); msgType.value = 'err'; return }
    showGen.value = false
    await load()
    msg.value = 'Certificate created'; msgType.value = 'ok'
  } catch (e) { msg.value = 'Generate error: ' + e.message; msgType.value = 'err' }
}

async function remove(c) {
  if (!confirm(`Delete ${c.name}?`)) return
  deleting.value = c.name
  try {
    const r = await fetch(`/api/system/certificates/${encodeURIComponent(c.name)}`, { method: 'DELETE' })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) { msg.value = 'Delete failed: ' + (d.detail || r.status); msgType.value = 'err' }
    else { await load(); msg.value = 'Deleted'; msgType.value = 'ok' }
  } catch (e) { msg.value = 'Delete error: ' + e.message; msgType.value = 'err' }
  deleting.value = ''
}

onMounted(load)
</script>

<style scoped>
.cert-page{display:flex;flex-direction:column;gap:12px}
h2{font-size:15px;color:var(--fg);font-weight:600}
.hint{font-size:11px;color:var(--fg3)}
.cert-actions{display:flex;gap:8px;align-items:center}
.gen-form{display:flex;gap:6px;flex-wrap:wrap;background:var(--bg2);padding:12px;border:1px solid var(--border);border-radius:3px}
.gen-form input{padding:5px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--mono);flex:1;min-width:100px}
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);font-size:11px}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--fg3);font-size:9px;text-transform:uppercase;letter-spacing:1px;background:var(--bg3)}
.mono{font-family:var(--mono)}
.empty{text-align:center;color:var(--fg3);padding:24px}
.muted{color:var(--fg3);font-size:10px}
.exp-badge{padding:2px 6px;border-radius:3px;font-size:10px;font-family:var(--mono)}
.exp-ok{color:var(--green);background:rgba(0,200,80,.08)}
.exp-soon{color:var(--accent);background:rgba(255,200,0,.08)}
.exp-warn{color:#ff9800;background:rgba(255,152,0,.12)}
.exp-expired{color:var(--red);background:rgba(255,0,0,.12)}
.exp-unknown{color:var(--fg3)}
.days{opacity:.7}
.usage{color:var(--accent);font-size:10px;font-family:var(--mono)}
.btn{padding:4px 12px;background:var(--bg3);color:var(--fg2);border:1px solid var(--border);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.btn-accent{background:var(--accent);color:#000;border-color:var(--accent)}
.btn-del{color:var(--red);border-color:rgba(255,0,0,.3);padding:2px 8px;font-size:10px}
.btn-del:disabled{opacity:.4}
.msg{font-size:11px;font-weight:500}.ok{color:var(--green)}.err{color:var(--red)}
</style>
