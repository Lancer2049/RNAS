<template>
  <div class="proto-monitor">
    <h2>Protocol Monitor</h2>
    <p class="hint">Real-time RADIUS/PPP protocol activity — parsed from accel-ppp log</p>

    <div class="stats-row">
      <div class="stat"><span class="label">Auth Sent</span><span class="value">{{ svc.auth_sent || 0 }}</span></div>
      <div class="stat"><span class="label">Acct Sent</span><span class="value">{{ svc.acct_sent || 0 }}</span></div>
      <div class="stat"><span class="label">Failures</span><span class="value" :class="(svc.radius_fail_count||0)>0?'red':''">{{ svc.radius_fail_count || 0 }}</span></div>
      <div class="stat"><span class="label">Active</span><span class="value green">{{ svc.sessions_active || 0 }}</span></div>
    </div>

    <div class="log-panel">
      <div class="log-row" v-for="(e,i) in events" :key="i">
        <span class="lt">{{ e.time.slice(11,19) }}</span>
        <span class="ldir" :class="e.direction">{{ e.direction === 'send' ? '»' : e.direction === 'recv' ? '«' : '\u2022' }}</span>
        <span class="ltype" :class="typeClass(e.type)">{{ fmtType(e.type) }}</span>
        <span class="lwho" v-if="e.username">{{ e.username }}</span>
        <span class="lip" v-if="e.ip">{{ e.ip }}</span>
        <span class="ldetail">{{ e.detail.slice(0, 120) }}{{ e.detail.length > 120 ? '\u2026' : '' }}</span>
      </div>
      <div v-if="!events.length" class="empty">Waiting for RADIUS activity...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const events = ref([])
const svc = ref({})
const knownKeys = new Set()
let timer = null

function typeClass(t) {
  if (!t) return ''
  if (t.includes('Accept') || t === 'auth_succeeded') return 't-ok'
  if (t.includes('Reject') || t === 'auth_failed') return 't-err'
  if (t.includes('Request') && t.includes('Access')) return 't-req'
  if (t.includes('Accounting')) return t.includes('Request') ? 't-acct' : 't-resp'
  if (t.includes('Disconnect')) return 't-err'
  return ''
}
function fmtType(t) {
  if (t === 'auth_succeeded') return 'AUTH OK'
  if (t === 'auth_failed') return 'AUTH FAIL'
  return t.toUpperCase().replace('-Request',' REQ').replace('-Response',' RESP').replace('-Accept',' ACC').replace('-Reject',' REJ')
}

async function fetchEvents() {
  try {
    const r = await fetch('/api/protocol/events?lines=50')
    const d = await r.json()
    const fresh = []
    for (const e of (d.events || [])) {
      const key = e.time + '_' + e.type + '_' + (e.id||'') + '_' + (e.username||'')
      if (!knownKeys.has(key)) {
        knownKeys.add(key)
        fresh.push(e)
      }
    }
    events.value = [...fresh.reverse(), ...events.value].slice(0, 100)
  } catch {}
}
async function fetchStats() {
  try { const r = await fetch('/api/status'); svc.value = (await r.json()).service || {} } catch {}
}

onMounted(() => {
  fetchEvents(); fetchStats()
  timer = setInterval(() => { fetchEvents(); fetchStats() }, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.proto-monitor { display:flex; flex-direction:column; gap:12px; }
h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.stats-row{display:flex;gap:14px}
.stat{background:var(--bg2);padding:10px 16px;border:1px solid var(--border);border-radius:3px;text-align:center;min-width:90px}
.label{display:block;font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.value{font-size:22px;font-weight:700;color:var(--fg)} .red{color:var(--red)} .green{color:var(--green)}
.log-panel{background:#0a0f14;border:1px solid var(--border);border-radius:3px;padding:8px;max-height:55vh;overflow-y:auto;font-family:var(--mono);font-size:10px}
.log-row{padding:3px 6px;border-bottom:1px solid rgba(46,64,82,0.25);display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.log-row:hover{background:rgba(10,189,227,0.03)}
.lt{color:var(--fg3);width:55px;flex-shrink:0;font-size:9px}
.ldir{font-size:12px;width:14px;text-align:center;flex-shrink:0}
.ldir.send{color:var(--accent)} .ldir.recv{color:var(--green)} .ldir.local{color:var(--fg3)}
.ltype{padding:0 5px;border-radius:2px;font-size:8px;font-weight:700;letter-spacing:.3px;min-width:48px;text-align:center;flex-shrink:0}
.t-ok{background:rgba(16,172,132,0.15);color:var(--green)}
.t-err{background:rgba(238,82,83,0.15);color:var(--red)}
.t-req{background:rgba(10,189,227,0.12);color:var(--accent)}
.t-acct{background:rgba(255,159,67,0.12);color:#ff9f43}
.t-resp{background:rgba(131,149,167,0.15);color:var(--fg2)}
.lwho{color:var(--accent);font-weight:600;flex-shrink:0}
.lip{color:var(--fg2);flex-shrink:0}
.ldetail{color:var(--fg3);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.empty{text-align:center;color:var(--fg3);padding:30px;font-size:11px}
</style>
