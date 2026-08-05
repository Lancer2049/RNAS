<template>
  <div class="sim-section">
    <h2>Fault Injection</h2>
    <p class="hint">Simulate network faults to test RADIUS server resilience</p>
    <div class="fault-grid">
      <div v-for="f in faults" :key="f.id" class="fault-card">
        <h3>{{ f.icon }} {{ f.name }}</h3>
        <p>{{ f.desc }}</p>
        <button @click="inject(f)" :disabled="f.active">{{ f.active ? 'Active...' : '▶ Inject' }}</button>
        <button v-if="f.active" class="btn-clear" @click="clear(f)">Clear</button>
        <span v-if="f.result" class="result" :class="f.result.ok?'ok':'fail'">{{ f.result.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const faults = ref([
  {id:'radius-timeout',icon:'⏱',name:'RADIUS Timeout',desc:'Block RADIUS port on VM2',active:false,result:null},
  {id:'radius-reject',icon:'🚫',name:'Auth Reject',desc:'Use invalid credentials',active:false,result:null},
  {id:'latency',icon:'🐌',name:'Network Latency',desc:'Add 200ms delay on VM3',active:false,result:null},
  {id:'packet-loss',icon:'📦',name:'Packet Loss',desc:'10% packet loss',active:false,result:null},
])
async function inject(f) { f.active=true;f.result=null; try{const r=await fetch(`/api/sim/fault/${f.id}`);const d=await r.json().catch(()=>({}));f.result={ok:r.ok && !!d.success,text:r.ok?'Injected':(d.detail||'Failed')};if(!(r.ok && !!d.success)){f.active=false}}catch(e){f.result={ok:false,text:'Failed'};f.active=false} }
async function clear(f) { try{const r=await fetch(`/api/sim/fault/clear`);f.active=false;f.result=r.ok?null:{ok:false,text:'Clear failed'} }catch{f.active=false;f.result={ok:false,text:'Clear failed'}} }
</script>

<style scoped>
.sim-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.fault-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px }
.fault-card { background:var(--bg2); padding:14px; border:1px solid var(--border); border-radius:3px; display:flex; flex-direction:column; gap:8px }
.fault-card h3 { font-size:13px; color:var(--fg) } .fault-card p { font-size:11px; color:var(--fg2); flex:1 }
.fault-card button { padding:5px 12px; border:none; border-radius:3px; cursor:pointer; font-size:11px; font-weight:600; font-family:var(--font); background:#ff9f43; color:#000 }
.fault-card button:disabled { opacity:0.4 } .btn-clear { background:var(--red) !important; color:#fff !important }
.result { font-size:11px; padding:4px 8px; border-radius:3px }
.result.ok { color:var(--green); background:rgba(16,172,132,0.1) } .result.fail { color:var(--red); background:rgba(238,82,83,0.1) }
</style>
