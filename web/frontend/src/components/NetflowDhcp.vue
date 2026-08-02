<template>
  <div class="section">
    <h2>NetFlow / sFlow</h2>
    <p class="hint">softflowd traffic export to collector (VM2:2055)</p>
    <div class="stats-row">
      <div class="stat"><span class="label">Service</span><span class="value" :class="nf.running?'up':'down'">{{ nf.running ? 'Running' : 'Stopped' }}</span></div>
      <div class="stat"><span class="label">Collector</span><span class="value mono">{{ nf.collector || 'N/A' }}</span></div>
      <div class="stat"><span class="label">Interface</span><span class="value mono">{{ nf.interface || 'N/A' }}</span></div>
      <div class="stat"><span class="label">Format</span><span class="value">{{ nf.format || 'N/A' }}</span></div>
    </div>

    <h3>DHCP Relay (RFC 3046)</h3>
    <p class="hint">Relays DHCP requests to upstream server with giaddr and optional Option 82 (Relay Agent Information)</p>
    <div class="stats-row">
      <div class="stat"><span class="label">Service</span><span class="value" :class="dhcp.running?'up':'down'">{{ dhcp.running ? 'Running' : 'Stopped' }}</span></div>
      <div class="stat"><span class="label">Enabled</span><span class="value" :class="form.enabled==='yes'?'up':'down'">{{ form.enabled==='yes' ? 'Yes' : 'No' }}</span></div>
      <div class="stat"><span class="label">Option 82</span><span class="value" :class="form.option82==='yes'?'up':'muted'">{{ form.option82==='yes' ? 'On' : 'Off' }}</span></div>
    </div>

    <div class="relay-form">
      <div class="field-row">
        <label>Enabled</label>
        <span class="toggle">
          <input type="checkbox" v-model="enabledBool" />
        </span>
      </div>
      <div class="field-row">
        <label>Upstream Server</label>
        <input v-model="form.upstream" placeholder="192.168.0.202" />
      </div>
      <div class="field-row">
        <label>GIADDR</label>
        <input v-model="form.giaddr" placeholder="192.168.100.1" />
      </div>
      <div class="field-row">
        <label>Interface</label>
        <input v-model="form.interface" placeholder="ens33" />
      </div>
      <div class="field-row">
        <label>Option 82</label>
        <span class="toggle">
          <input type="checkbox" v-model="option82Bool" />
        </span>
      </div>
      <div v-if="option82Bool" class="opt82-fields">
        <div class="field-row">
          <label>Circuit ID</label>
          <input v-model="form.circuit_id" placeholder="rnas-port1" />
        </div>
        <div class="field-row">
          <label>Remote ID</label>
          <input v-model="form.remote_id" placeholder="rnas" />
        </div>
      </div>
      <div class="form-actions">
        <button class="btn-primary" @click="save">Save &amp; Restart</button>
        <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
const nf = ref({ running: false, collector: '', interface: '', format: '' })
const dhcp = ref({ running: false, upstream: '', giaddr: '' })
const form = reactive({ enabled: 'no', upstream: '', giaddr: '', interface: '', option82: 'no', circuit_id: '', remote_id: '' })
const msg = ref(''), msgType = ref('ok')

const enabledBool = computed({
  get: () => form.enabled === 'yes',
  set: v => { form.enabled = v ? 'yes' : 'no' },
})
const option82Bool = computed({
  get: () => form.option82 === 'yes',
  set: v => { form.option82 = v ? 'yes' : 'no' },
})

async function load() {
  try { const r = await fetch('/api/netflow'); nf.value = await r.json() } catch {}
  try {
    const r = await fetch('/api/dhcp-relay')
    const d = await r.json()
    dhcp.value = d
    Object.assign(form, {
      enabled: d.enabled || 'no', upstream: d.upstream || '',
      giaddr: d.giaddr || '', interface: d.interface || '',
      option82: d.option82 || 'no',
      circuit_id: d.circuit_id || 'rnas-port1', remote_id: d.remote_id || 'rnas',
    })
  } catch {}
}

async function save() {
  msg.value = ''
  try {
    const r = await fetch('/api/dhcp-relay', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form }),
    })
    if (!r.ok) {
      const err = await r.json().catch(() => ({}))
      msg.value = 'Save failed: ' + (err.detail || r.status)
      msgType.value = 'err'
      return
    }
    msg.value = 'Relay config saved'
    msgType.value = 'ok'
    await load()
  } catch (e) {
    msg.value = 'Save failed: ' + (e.message || e)
    msgType.value = 'err'
  }
}

onMounted(load)
</script>

<style scoped>
.section { display:flex; flex-direction:column; gap:12px; }
h2{font-size:15px;color:var(--fg);font-weight:600}
h3{font-size:12px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px}
.hint{font-size:11px;color:var(--fg3)}
.stats-row { display:flex; gap:14px; background:var(--bg2); padding:10px 14px; border:1px solid var(--border); border-radius:3px; flex-wrap:wrap }
.stat { display:flex; flex-direction:column; gap:4px }
.label { font-size:10px; color:var(--fg3); text-transform:uppercase; letter-spacing:1px }
.value { font-size:14px; font-weight:600; color:var(--fg) }
.value.up { color:var(--green) } .value.down { color:var(--red) } .value.muted { color:var(--fg3) }
.mono { font-family:var(--mono) }
.relay-form { background:var(--bg2); border:1px solid var(--border); padding:12px 14px; border-radius:3px; display:flex; flex-direction:column; gap:8px; max-width:520px }
.field-row { display:flex; align-items:center; gap:10px; }
.field-row label { width:130px; font-size:11px; color:var(--fg2); text-transform:uppercase; letter-spacing:1px }
.field-row input { flex:1; padding:4px 8px; border:1px solid var(--border); border-radius:3px; font-size:11px; background:var(--bg); color:var(--fg); font-family:var(--mono) }
.toggle input { width:auto; }
.opt82-fields { display:flex; flex-direction:column; gap:8px; margin-left:140px; padding-left:0; }
.form-actions { display:flex; align-items:center; gap:10px; margin-top:4px }
.btn-primary { padding:5px 14px; background:var(--accent); color:#000; border:none; border-radius:3px; cursor:pointer; font-size:11px; font-weight:600; font-family:var(--font) }
.btn-primary:hover { filter:brightness(1.1) }
.msg { font-size:11px; font-weight:500 }
.msg.ok { color:var(--green) } .msg.err { color:var(--red) }
</style>
