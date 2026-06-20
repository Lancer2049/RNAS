<template>
  <div class="sim-section">
    <h2 class="page-title">Subscriber Simulation</h2>
    <p class="page-hint">Simulate multiple CPE clients connecting via various protocols</p>

    <div class="controls">
      <div class="field"><label>Protocol</label><select v-model="proto"><option v-for="p in protocols" :key="p" :value="p">{{ p.toUpperCase() }}</option></select></div>
      <div class="field"><label>Count</label><input v-model.number="count" type="number" min="1" max="50" /></div>
      <div class="field"><label>User</label><input v-model="user" /></div>
      <div class="field"><label>Pass</label><input v-model="pass" /></div>
      <button class="btn-start" @click="startSim" :disabled="running">{{ running ? 'Running...' : '▶ Start' }}</button>
      <button class="btn-stop" @click="stopSim" :disabled="!running">⏹ Stop</button>
      <span class="status" :class="running?'active':'idle'">{{ running ? 'Simulation active' : 'Ready' }}</span>
    </div>

    <div class="progress" v-if="running">
      <div class="bar"><div class="fill" :style="{width: (done*100/count)+'%'}"></div></div>
      <span>{{ passed }}/{{ done }} of {{ count }} ({{ failed }} failed)</span>
    </div>

    <div class="results" v-if="results.length">
      <table>
        <thead><tr><th>#</th><th>Proto</th><th>Status</th><th>IP</th><th>Latency</th></tr></thead>
        <tbody>
          <tr v-for="r in results" :key="r.id" :class="r.ok?'row-ok':'row-fail'">
            <td>{{ r.id }}</td><td>{{ r.proto }}</td>
            <td>{{ r.ok ? '✅' : '❌' }}</td>
            <td class="mono">{{ r.ip||'-' }}</td><td>{{ r.latency ? r.latency+'ms' : '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="!running" class="empty-state">
      <div class="icon">👥</div>
      <div class="text">No simulation running</div>
      <div class="sub">Configure parameters above and click Start to simulate subscriber connections</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const protocols = ['pppoe','pptp','l2tp','sstp']
const proto = ref('pppoe'), count = ref(5), user = ref('testuser'), pass = ref('testpass')
const running = ref(false), results = ref([]), done = ref(0), passed = ref(0), failed = ref(0)

async function startSim() {
  running.value = true; results.value = []; done.value = 0; passed.value = 0; failed.value = 0
  for (let i = 1; i <= count.value; i++) {
    const start = Date.now()
    try {
      const res = await fetch(`/api/sim/connect?proto=${proto.value}&user=${user.value}&pass=${pass.value}`)
      const d = await res.json()
      const ok = d.success
      results.value.push({id:i, proto:proto.value, ok, ip:d.ip, latency: Date.now()-start})
      done.value++; if (ok) passed.value++; else failed.value++
    } catch(e) {
      results.value.push({id:i, proto:proto.value, ok:false, latency: Date.now()-start})
      done.value++; failed.value++
    }
  }
  running.value = false
}
async function stopSim() {
  await fetch('/api/sim/stop')
  running.value = false
}
</script>

<style scoped>
.sim-section { display:flex; flex-direction:column; gap:12px; }
.page-title{font-size:15px;color:var(--fg);font-weight:600} .page-hint{font-size:11px;color:var(--fg3)}
.controls { display:flex; gap:10px; align-items:flex-end; flex-wrap:wrap; background:var(--bg2); padding:12px; border:1px solid var(--border); border-radius:3px }
.field { display:flex; flex-direction:column; gap:2px }
.field label { font-size:9px; color:var(--fg3); text-transform:uppercase; letter-spacing:1px }
.field input, .field select { padding:5px 8px; border:1px solid var(--border); border-radius:3px; font-size:12px; width:90px; background:var(--bg); color:var(--fg); font-family:var(--font); outline:none }
.field input:focus,.field select:focus { border-color:var(--accent) }
.btn-start { padding:6px 16px; background:var(--green); color:#000; border:none; border-radius:3px; cursor:pointer; font-size:12px; font-weight:600; font-family:var(--font) }
.btn-stop { padding:6px 16px; background:var(--red); color:#fff; border:none; border-radius:3px; cursor:pointer; font-size:12px; font-weight:600; font-family:var(--font) }
.btn-start:disabled,.btn-stop:disabled { opacity:0.4 }
.status { font-weight:600; font-size:12px } .active { color:var(--green) } .idle { color:var(--fg3) }
.progress { display:flex; align-items:center; gap:12px }
.bar { flex:1; height:6px; background:var(--bg3); border-radius:3px; overflow:hidden }
.fill { height:100%; background:var(--accent); transition:width .3s }
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);border-radius:3px;font-size:12px}
th,td{padding:5px 10px;text-align:left;border-bottom:1px solid var(--border)} th{color:var(--fg3);font-size:10px;text-transform:uppercase;letter-spacing:1px}
.row-ok { color:var(--fg) } .row-fail { background:rgba(238,82,83,0.04) }
.mono{font-family:var(--mono);font-size:11px}
.empty-state{text-align:center;padding:40px;color:var(--fg3)}.empty-state .icon{font-size:36px}.empty-state .text{font-size:13px;color:var(--fg2)}.empty-state .sub{font-size:11px}
</style>
