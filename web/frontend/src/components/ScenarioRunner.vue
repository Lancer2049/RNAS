<template>
  <div class="sim-section">
    <h2>Scenario Runner</h2>
    <p class="hint">Run predefined test scenarios with one click</p>
    <div class="scenario-grid">
      <div v-for="s in scenarios" :key="s.id" class="scenario-card" :class="{running: s.running}">
        <h3>{{ s.name }}</h3>
        <p>{{ s.description }}</p>
        <button @click="runScenario(s)" :disabled="s.running">{{ s.running ? 'Running...' : '▶ Run' }}</button>
        <span v-if="s.result" class="result" :class="s.result.ok?'ok':'fail'">{{ s.result.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const scenarios = ref([])
async function load() { try{const r=await fetch('/api/scenarios');scenarios.value=((await r.json()).scenarios||[]).map(s=>({...s,running:false,result:null}))}catch{} }
async function runScenario(s) {
  s.running=true; s.result=null
  try{const r=await fetch(`/api/scenarios/${s.id}/load`,{method:'POST'});const d=await r.json();s.result={ok:d.success,text:d.success?`${d.applied}/${d.total} applied`:'Failed'}}catch{}
  s.running=false
}
onMounted(load)
</script>

<style scoped>
.sim-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.scenario-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:10px }
.scenario-card { background:var(--bg2); padding:14px; border:1px solid var(--border); border-radius:3px; display:flex; flex-direction:column; gap:8px }
.scenario-card h3 { font-size:13px; color:var(--fg) } .scenario-card p { font-size:11px; color:var(--fg2); flex:1 }
.scenario-card button { padding:5px 14px; background:var(--bg3); color:var(--accent); border:1px solid var(--accent); border-radius:3px; cursor:pointer; font-size:11px; font-weight:600; font-family:var(--font) }
.scenario-card button:hover { background:var(--accent); color:#000 }
.scenario-card button:disabled { opacity:0.4 }
.result { font-size:11px; padding:4px 8px; border-radius:3px }
.result.ok { color:var(--green); background:rgba(16,172,132,0.1) } .result.fail { color:var(--red); background:rgba(238,82,83,0.1) }
.running { border-left:3px solid var(--accent) }
</style>
