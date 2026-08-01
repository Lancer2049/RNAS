<template>
  <div class="session-detail" v-if="session">
    <div class="back-row"><a @click="$emit('back')" class="back-link">← Back to Sessions</a></div>
    <h2 class="page-title">Session: {{ session.username || session.sid }}</h2>
    
    <div class="detail-grid">
      <div class="card"><label>SID</label><span class="mono">{{ session.sid }}</span></div>
      <div class="card"><label>Username</label><span>{{ session.username||'-' }}</span></div>
      <div class="card"><label>IP Address</label><span class="mono">{{ session.ip||'-' }}</span></div>
      <div class="card"><label>Protocol</label><span class="type-badge">{{ session.type||'-' }}</span></div>
      <div class="card"><label>State</label><span class="badge" :class="session.state">{{ session.state||'active' }}</span></div>
      <div class="card"><label>Interface</label><span>{{ session.ifname||'-' }}</span></div>
      <div class="card"><label>Caller-ID</label><span class="mono">{{ session.calling_sid||session.sid }}</span></div>
      <div class="card"><label>Uptime</label><span>{{ fmtUptime(session.uptime_raw) }}</span></div>
      <div class="card"><label>RX Bytes</label><span>{{ fmtBytes(session.rx_bytes_raw) }}</span></div>
      <div class="card"><label>TX Bytes</label><span>{{ fmtBytes(session.tx_bytes_raw) }}</span></div>
    </div>

    <div class="actions-section">
      <h3>Actions</h3>
      <div class="action-row">
        <button class="btn-primary" @click="disconnectSession">Disconnect</button>
        <button class="btn-primary" @click="refreshSession">Refresh</button>
      </div>
    </div>

    <div class="coa-section" v-if="session.state==='active'">
      <h3>CoA Modification</h3>
      <p class="hint">Change session attributes via RADIUS CoA (RFC 3576)</p>
      <div class="coa-form">
        <div class="field"><label>Rate Limit</label><input v-model="coaRate" placeholder="e.g. 10M/20M" /></div>
        <div class="field"><label>Session Timeout</label><input v-model="coaTimeout" placeholder="seconds" type="number" /></div>
        <button class="btn-primary" @click="sendCoA" :disabled="coaSending">{{ coaSending ? 'Sending...' : 'Send CoA' }}</button>
        <span v-if="coaResult" class="coa-result" :class="coaOk?'ok':'fail'">{{ coaResult }}</span>
      </div>
    </div>
  </div>
  <div v-else class="empty-state"><div class="icon">🔍</div><div class="text">No session selected</div></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps({ session: Object })
defineEmits(['back'])

const session = ref(props.session)
const coaRate = ref(''), coaTimeout = ref(''), coaSending = ref(false), coaResult = ref(''), coaOk = ref(false)

async function disconnectSession() {
  if (!session.value?.sid) return
  await fetch(`/api/sessions/${session.value.sid}/disconnect`, { method: 'POST' })
  session.value.state = 'finishing'
}

async function refreshSession() {
  const r = await fetch('/api/status')
  const d = await r.json()
  const found = (d.sessions||[]).find(s => s.sid === session.value?.sid)
  if (found) session.value = found
}

async function sendCoA() {
  if (!session.value?.username) return
  coaSending.value = true; coaResult.value = ''
  let attrs = `User-Name=${session.value.username}`
  if (coaRate.value) attrs += `,Mikrotik-Rate-Limit=${coaRate.value}`
  if (coaTimeout.value) attrs += `,Session-Timeout=${coaTimeout.value}`
  try {
    const r = await fetch(`/api/tools/coa?user=${encodeURIComponent(session.value.username)}&attrs=${encodeURIComponent(attrs.replace(`User-Name=${session.value.username},`,''))}`)
    const d = await r.json()
    coaOk.value = d.output?.includes('ACK')
    coaResult.value = coaOk.value ? 'CoA ACK — attributes changed' : 'CoA NAK — check logs'
  } catch { coaResult.value = 'CoA request failed' }
  coaSending.value = false
}

function fmtBytes(n){if(!n)return'0B';if(n<1024)return n+'B';return n<1e6?(n/1024).toFixed(1)+'K':(n/1e6).toFixed(1)+'M'}
function fmtUptime(r){if(!r)return'-';const s=parseInt(r);if(isNaN(s))return r;if(s<60)return s+'s';if(s<3600)return Math.floor(s/60)+'m';return Math.floor(s/3600)+'h'}
</script>

<style scoped>
.session-detail{display:flex;flex-direction:column;gap:16px}
.back-row{margin-bottom:4px} .back-link{color:var(--accent);cursor:pointer;font-size:13px} .back-link:hover{text-decoration:underline}
.detail-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.card{background:var(--bg2);padding:14px 16px;border:1px solid var(--border);border-radius:3px;display:flex;flex-direction:column;gap:4px}
.card label{font-size:9px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.card span{font-size:14px;font-weight:600;color:var(--fg)} .mono{font-family:var(--mono);font-size:13px!important}
.type-badge{background:rgba(10,189,227,0.12);color:var(--accent);padding:2px 8px;border-radius:3px;font-size:11px;display:inline-block;width:fit-content}
.badge{padding:2px 10px;border-radius:10px;font-size:10px;font-weight:600;display:inline-block;width:fit-content}
.badge.active{background:rgba(16,172,132,0.12);color:var(--green)} .badge.finishing{background:rgba(255,159,67,0.12);color:#ff9f43}
.actions-section h3,.coa-section h3{font-size:13px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.action-row{display:flex;gap:8px}
.hint{font-size:11px;color:var(--fg3);margin-bottom:8px}
.coa-form{display:flex;gap:10px;align-items:flex-end;background:var(--bg2);padding:14px;border:1px solid var(--border);border-radius:3px;flex-wrap:wrap}
.field{display:flex;flex-direction:column;gap:3px} .field label{font-size:9px;color:var(--fg3);text-transform:uppercase}
.field input{padding:5px 10px;border:1px solid var(--border);border-radius:3px;font-size:12px;width:140px;background:var(--bg);color:var(--fg);font-family:var(--font);outline:none}
.field input:focus{border-color:var(--accent)}
.coa-result{font-size:12px;font-weight:600} .ok{color:var(--green)} .fail{color:var(--red)}
.btn-primary{padding:6px 16px;background:var(--bg3);color:var(--accent);border:1px solid var(--accent);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.btn-primary:hover{background:var(--accent);color:#000}
.btn-primary:disabled{opacity:.4;cursor:not-allowed}
</style>
