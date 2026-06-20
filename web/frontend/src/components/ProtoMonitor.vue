<template>
  <div class="proto-monitor">
    <h2>Protocol Monitor</h2>
    <p class="hint">Real-time RADIUS/PPP protocol activity</p>

    <div class="stats-row">
      <div class="stat"><span class="label">Auth Sent</span><span class="value">{{ service.auth_sent || 0 }}</span></div>
      <div class="stat"><span class="label">Acct Sent</span><span class="value">{{ service.acct_sent || 0 }}</span></div>
      <div class="stat"><span class="label">Failures</span><span class="value" :class="service.radius_fail_count>0?'red':''">{{ service.radius_fail_count || 0 }}</span></div>
      <div class="stat"><span class="label">Active</span><span class="value green">{{ service.sessions_active || 0 }}</span></div>
    </div>

    <div class="log-panel">
      <div class="log-item" v-for="(l,i) in events" :key="i">
        <span class="time">{{ l.time }}</span>
        <span class="type" :class="l.type">{{ l.type }}</span>
        <span>{{ l.detail }}</span>
      </div>
      <div v-if="!events.length" class="empty">Waiting for RADIUS activity...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const service = ref({})
const events = ref([])
let ws = null

async function startWS() {
  try {
    ws = new WebSocket(`ws://${location.host}/api/ws`)
    ws.onmessage = e => {
      try {
        const d = JSON.parse(e.data)
        const oldSvc = {auth_sent: service.value.auth_sent||0, acct_sent: service.value.acct_sent||0}
        service.value = d.service || {}
        if ((d.service?.auth_sent||0) > (oldSvc.auth_sent||0))
          events.value.unshift({time:new Date().toLocaleTimeString(),type:'auth',detail:`Access-Request sent (total: ${d.service.auth_sent})`})
        if ((d.service?.acct_sent||0) > (oldSvc.acct_sent||0))
          events.value.unshift({time:new Date().toLocaleTimeString(),type:'acct',detail:`Accounting-Request sent (total: ${d.service.acct_sent})`})
        if (events.value.length > 50) events.value.length = 50
      } catch {}
    }
    ws.onclose = () => ws = null
  } catch {}
}
onMounted(startWS)
onUnmounted(() => ws?.close())
</script>

<style scoped>
.proto-monitor { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.stats-row { display:flex; gap:14px }
.stat { background:var(--bg2); padding:10px 16px; border:1px solid var(--border); border-radius:3px; text-align:center; min-width:90px }
.label { display:block; font-size:10px; color:var(--fg3); text-transform:uppercase; letter-spacing:1px }
.value { font-size:22px; font-weight:700; color:var(--fg) } .red{color:var(--red)} .green{color:var(--green)}
.log-panel { background:#0a0f14; border:1px solid var(--border); border-radius:3px; padding:12px; max-height:400px; overflow-y:auto; font-family:var(--mono); font-size:11px }
.log-item { padding:4px 0; border-bottom:1px solid rgba(46,64,82,0.3); display:flex; gap:12px; color:var(--fg2) }
.time { color:var(--fg3); width:80px; flex-shrink:0 }
.type { padding:0 6px; border-radius:3px; font-size:9px; font-weight:600; width:50px; text-align:center }
.type.auth { background:rgba(59,130,246,0.2); color:#60a5fa }
.type.acct { background:rgba(34,197,94,0.2); color:#4ade80 }
.empty { text-align:center; color:var(--fg3); padding:40px; font-size:12px }
</style>
