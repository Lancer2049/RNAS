<template>
  <div class="tool-section">
    <h2>Scheduler</h2>
    <p class="hint">Automated test runs — run regression/benchmark on schedule</p>
    <div class="add-form">
      <input v-model="newName" placeholder="Task name" class="field" />
      <select v-model="newAction" class="field">
        <option value="regression">Regression Test</option>
        <option value="benchmark">Benchmark</option>
        <option value="vsa-smoke">VSA Smoke Test</option>
      </select>
      <input v-model="newInterval" placeholder="Interval (minutes)" type="number" class="field" min="1" />
      <button @click="addTask" class="btn-add">+ Add</button>
    </div>
    <table v-if="tasks.length">
      <thead><tr><th>Name</th><th>Action</th><th>Interval</th><th>Last Run</th><th>Next Run</th><th></th></tr></thead>
      <tbody>
        <tr v-for="t in tasks" :key="t.name"><td>{{ t.name }}</td><td>{{ t.action }}</td><td>{{ t.interval }}m</td><td>{{ t.last || '-' }}</td><td>{{ t.next || '-' }}</td><td><button @click="removeTask(t.name)" class="btn-del">✕</button></td></tr>
      </tbody>
    </table>
    <div v-else class="empty">No scheduled tasks</div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'
const tasks = reactive([]), newName=ref(''), newAction=ref('regression'), newInterval=ref(60)
async function loadTasks() {
  try { const r = await fetch('/api/scheduler'); tasks.length = 0; tasks.push(...((await r.json()).tasks || [])) } catch {}
}
async function saveTasks() {
  fetch('/api/scheduler', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tasks: [...tasks] }) })
}
function addTask(){if(!newName.value)return;tasks.push({name:newName.value,action:newAction.value,interval:newInterval.value,last:'',next:new Date(Date.now()+newInterval.value*60000).toLocaleTimeString()});newName.value='';saveTasks()}
function removeTask(name){const i=tasks.findIndex(t=>t.name===name);if(i>=0){tasks.splice(i,1);saveTasks()}}
onMounted(loadTasks)
</script>
<style scoped>
.tool-section{display:flex;flex-direction:column;gap:12px} h2{font-size:15px;color:var(--fg);font-weight:600} .hint{font-size:11px;color:var(--fg3)}
.add-form{display:flex;gap:6px;flex-wrap:wrap;background:var(--bg2);padding:10px;border:1px solid var(--border);border-radius:3px}
.field{padding:5px 8px;border:1px solid var(--border);border-radius:3px;font-size:12px;background:var(--bg);color:var(--fg);font-family:var(--font);outline:none}
.field:focus{border-color:var(--accent)}
.btn-add{padding:5px 14px;background:var(--green);color:#000;border:none;border-radius:3px;cursor:pointer;font-size:11px;font-weight:600;font-family:var(--font)}
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);border-radius:3px;font-size:12px}
th,td{padding:5px 10px;text-align:left;border-bottom:1px solid var(--border)} th{color:var(--fg3);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:1px}
.btn-del{padding:2px 6px;background:rgba(238,82,83,0.08);border:1px solid rgba(238,82,83,0.3);border-radius:3px;cursor:pointer;font-size:11px;color:var(--red)}
.btn-del:hover{background:var(--red);color:#fff}
.empty{text-align:center;color:var(--fg3);padding:30px;font-size:12px}
</style>
