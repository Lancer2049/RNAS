<template>
  <div class="queue-section">
    <h2>Queue Management</h2>
    <p class="hint">Bandwidth control — Simple Queue rules</p>

    <div class="add-form">
      <input v-model="newName" placeholder="Name" class="field" />
      <input v-model="newTarget" placeholder="Target IP" class="field" />
      <input v-model="newRate" placeholder="Rate (e.g. 10M/20M)" class="field" />
      <select v-model="newProto" class="field"><option value="all">All</option><option>pppoe</option><option>l2tp</option><option>sstp</option></select>
      <button @click="addQueue" class="btn-add">+ Add</button>
    </div>

    <table v-if="queues.length">
      <thead><tr><th>Name</th><th>Target</th><th>Rate</th><th>Burst</th><th>TX</th><th>RX</th><th>Status</th><th></th></tr></thead>
      <tbody>
        <tr v-for="q in queues" :key="q.name">
          <td class="mono">{{ q.name }}</td>
          <td>{{ q.target }}</td>
          <td class="mono">{{ q.rate }}</td>
          <td class="mono">{{ q.burst||'none' }}</td>
          <td>{{ formatBytes(q.tx) }}</td>
          <td>{{ formatBytes(q.rx) }}</td>
          <td><span class="badge" :class="q.active?'active':'inactive'">{{ q.active?'Active':'Idle' }}</span></td>
          <td><button @click="removeQueue(q.name)" class="btn-del">✕</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state">
      <div class="icon">📏</div>
      <div class="text">No queue rules defined</div>
      <div class="sub">Add bandwidth control rules above to manage traffic shaping</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
const queues = reactive([])
const newName = ref(''), newTarget = ref(''), newRate = ref('10M'), newProto = ref('all')

async function loadQueues() {
  try { const r = await fetch('/api/queues'); const d = await r.json(); queues.length=0; queues.push(...(d.queues||[])) } catch {}
}
function addQueue() {
  if (!newName.value||!newTarget.value) return
  queues.push({name:newName.value, target:newTarget.value, rate:newRate.value, burst:'', tx:0, rx:0, active:true, proto:newProto.value})
  newName.value=''; newTarget.value=''; newRate.value='10M'
  fetch('/api/queues',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({queues:[...queues]})})
}
function removeQueue(name) {
  const i = queues.findIndex(q=>q.name===name)
  if (i>=0) { queues.splice(i,1); fetch('/api/queues',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({queues:[...queues]})}) }
}
function formatBytes(n){if(!n)return'0B';if(n<1024)return n+'B';if(n<1e6)return(n/1024).toFixed(1)+'K';return(n/1e6).toFixed(1)+'M'}
onMounted(loadQueues)
</script>

<style scoped>
.queue-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.add-form { display:flex; gap:6px; flex-wrap:wrap; background:var(--bg2); padding:10px; border:1px solid var(--border); border-radius:3px }
.field { padding:5px 8px; border:1px solid var(--border); border-radius:3px; font-size:12px; background:var(--bg); color:var(--fg); font-family:var(--font); outline:none }
.field:focus { border-color:var(--accent) }
.btn-add { padding:5px 14px; background:var(--green); color:#000; border:none; border-radius:3px; cursor:pointer; font-size:11px; font-weight:600; font-family:var(--font) }
.btn-add:hover { opacity:.85 }
table { width:100%; border-collapse:collapse; background:var(--bg2); border:1px solid var(--border); border-radius:3px; font-size:12px }
th,td { padding:5px 10px; text-align:left; border-bottom:1px solid var(--border) } th { color:var(--fg3); font-weight:600; font-size:10px; text-transform:uppercase; letter-spacing:1px }
.mono { font-family:var(--mono); font-size:11px }
.badge { padding:2px 8px; border-radius:10px; font-size:10px }
.badge.active { background:rgba(16,172,132,0.12); color:var(--green) } .badge.inactive { background:var(--bg3); color:var(--fg3) }
.btn-del { padding:2px 6px; background:rgba(238,82,83,0.08); border:1px solid rgba(238,82,83,0.3); border-radius:3px; cursor:pointer; font-size:11px; color:var(--red) }
.btn-del:hover { background:var(--red); color:#fff }
.empty{text-align:center;color:var(--fg3);padding:30px;font-size:12px}
.empty-state{text-align:center;padding:40px;color:var(--fg3)}.empty-state .icon{font-size:36px}.empty-state .text{font-size:13px;color:var(--fg2)}.empty-state .sub{font-size:11px}
</style>
