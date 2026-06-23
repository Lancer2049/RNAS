<template>
  <div class="quickset">
    <div class="qs-header">
      <h2>⚡ Quick Setup</h2>
      <p class="hint">Configure RNAS in 3 steps — Step {{ step }} of 3</p>
    </div>

    <div class="qs-steps">
      <div class="qs-step" :class="{active: step===1, done: step>1}"><span class="qs-num">1</span> Network</div>
      <div class="qs-connector" :class="{done: step>1}"></div>
      <div class="qs-step" :class="{active: step===2, done: step>2}"><span class="qs-num">2</span> RADIUS</div>
      <div class="qs-connector" :class="{done: step>2}"></div>
      <div class="qs-step" :class="{active: step===3, done: step>3}"><span class="qs-num">3</span> Protocols</div>
    </div>

    <!-- Step 1: Network -->
    <div v-if="step===1" class="qs-form">
      <div class="field"><label>PPPoE Interface</label><input v-model="cfg.pppoe_iface" placeholder="ens33" /></div>
      <div class="field"><label>LAN Gateway IP</label><input v-model="cfg.lan_ip" placeholder="192.168.100.1/24" /></div>
      <div class="field"><label>AC Name</label><input v-model="cfg.ac_name" placeholder="RNAS" /></div>
      <div class="field"><label>IP Pool Start</label><input v-model="cfg.ip_pool_start" placeholder="192.168.100.10" /></div>
      <div class="field"><label>IP Pool End</label><input v-model="cfg.ip_pool_end" placeholder="192.168.100.200" /></div>
      <button class="btn-next" @click="step=2">Next →</button>
    </div>

    <!-- Step 2: RADIUS -->
    <div v-if="step===2" class="qs-form">
      <div class="field"><label>RADIUS Server</label><input v-model="cfg.radius_server" placeholder="192.168.0.202" /></div>
      <div class="field"><label>RADIUS Secret</label><input v-model="cfg.radius_secret" type="password" placeholder="testing123" /></div>
      <div class="qs-actions"><button class="btn-prev" @click="step=1">← Back</button><button class="btn-next" @click="step=3">Next →</button></div>
    </div>

    <!-- Step 3: Confirm & Apply -->
    <div v-if="step===3" class="qs-form">
      <div class="qs-summary">
        <div><span>Interface</span><span class="mono">{{ cfg.pppoe_iface }}</span></div>
        <div><span>Gateway</span><span class="mono">{{ cfg.lan_ip }}</span></div>
        <div><span>RADIUS</span><span class="mono">{{ cfg.radius_server }}</span></div>
        <div><span>Pool</span><span class="mono">{{ cfg.ip_pool_start }} – {{ cfg.ip_pool_end }}</span></div>
      </div>
      <div class="qs-actions">
        <button class="btn-prev" @click="step=2">← Back</button>
        <button class="btn-apply" @click="apply" :disabled="applying">{{ applying ? 'Applying...' : 'Apply Configuration' }}</button>
      </div>
      <div v-if="result" class="qs-result" :class="result.status==='applied'?'ok':'err'">{{ result.status || result.error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const step = ref(1)
const applying = ref(false)
const result = ref(null)
const cfg = ref({
  pppoe_iface: 'ens33', lan_ip: '192.168.100.1/24', ac_name: 'RNAS',
  ip_pool_start: '192.168.100.10', ip_pool_end: '192.168.100.200',
  radius_server: '192.168.0.202', radius_secret: 'testing123'
})

async function apply() {
  applying.value = true; result.value = null
  try {
    const r = await fetch('/api/setup/apply', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg.value) })
    result.value = await r.json()
  } catch(e) { result.value = { status: 'error', error: e.message } }
  applying.value = false
}
</script>

<style scoped>
.quickset{display:flex;flex-direction:column;gap:16px;max-width:600px;margin:0 auto}
.qs-header h2{font-size:18px;color:var(--fg);font-weight:700}
.hint{font-size:12px;color:var(--fg3);margin-top:4px}
.qs-steps{display:flex;align-items:center;gap:8px;padding:16px 0}
.qs-step{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--fg3)}
.qs-step.active{color:var(--accent);font-weight:600}
.qs-step.done{color:var(--green)}
.qs-num{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;background:var(--bg3);color:var(--fg)}
.qs-step.active .qs-num,.qs-step.done .qs-num{background:var(--accent);color:#000}
.qs-connector{width:24px;height:2px;background:var(--border)}.qs-connector.done{background:var(--green)}
.qs-form{background:var(--bg2);padding:20px;border:1px solid var(--border);border-radius:4px;display:flex;flex-direction:column;gap:12px}
.field{display:flex;flex-direction:column;gap:4px}
.field label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.field input{padding:8px 12px;border:1px solid var(--border);border-radius:3px;font-size:13px;background:var(--bg);color:var(--fg);font-family:var(--mono);outline:none}
.field input:focus{border-color:var(--accent)}
.qs-actions{display:flex;gap:8px;margin-top:8px}
.btn-prev,.btn-next,.btn-apply{padding:8px 20px;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--font);border:none}
.btn-prev{background:var(--bg3);color:var(--fg2)}
.btn-next{background:var(--accent);color:#000;margin-left:auto}
.btn-apply{background:var(--green);color:#000;margin-left:auto}
.btn-apply:disabled{opacity:0.4}
.qs-summary{display:flex;flex-direction:column;gap:8px;background:var(--bg);padding:12px;border-radius:3px}
.qs-summary div{display:flex;justify-content:space-between;font-size:12px;color:var(--fg)}
.qs-summary span:first-child{color:var(--fg3)}
.mono{font-family:var(--mono)}
.qs-result{padding:10px;border-radius:3px;font-size:12px;text-align:center}
.qs-result.ok{background:rgba(16,172,132,0.1);color:var(--green)}
.qs-result.err{background:rgba(238,82,83,0.1);color:var(--red)}
</style>
