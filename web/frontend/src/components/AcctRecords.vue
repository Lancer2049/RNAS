<template>
  <div class="data-section">
    <h2>Accounting Records</h2>
    <p class="hint">RADIUS accounting data (radacct) — session history</p>
    <button class="btn-refresh" @click="load" :disabled="loading">{{ loading ? '...' : 'Refresh' }}</button>
    <button class="btn-export" @click="exportCSV" v-if="records.length">📥 CSV</button>
    <div class="table-wrap">
      <table v-if="records.length">
        <thead><tr><th>ID</th><th>User</th><th>NAS</th><th>Start</th><th>Stop</th><th>Dur</th><th>IP</th><th>RX</th><th>TX</th><th>Cause</th></tr></thead>
        <tbody>
          <tr v-for="r in records" :key="r.id">
            <td class="mono">{{ r.id }}</td><td>{{ r.username }}</td><td>{{ r.nas }}</td>
            <td class="mono">{{ fmtTime(r.start) }}</td><td class="mono">{{ fmtTime(r.stop) }}</td>
            <td>{{ fmtDur(r.duration) }}</td><td class="mono">{{ r.ip }}</td>
            <td>{{ fmtBytes(r.rx) }}</td><td>{{ fmtBytes(r.tx) }}</td>
            <td><span class="cause">{{ r.cause||'-' }}</span></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">Loading...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const records = ref([])
const loading = ref(false)
async function load() { loading.value=true; try{const r=await fetch('/api/aaa/acct');records.value=(await r.json()).records||[]}catch{};loading.value=false }
function exportCSV() {
  const hdr = 'ID,User,NAS,Start,Stop,Duration,IP,RX,TX,Cause\n'
  const rows = records.value.map(r => [r.id,r.username,r.nas,r.start,r.stop,r.duration,r.ip,r.rx,r.tx,r.cause].join(',')).join('\n')
  const blob = new Blob([hdr+rows],{type:'text/csv'})
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='radacct.csv'; a.click()
}
function fmtTime(t){return t?(t.split('.')[0]||t):'-'}
function fmtDur(s){if(!s||s==='0')return'-';const n=parseInt(s);if(n<60)return n+'s';if(n<3600)return Math.floor(n/60)+'m';if(n<86400)return Math.floor(n/3600)+'h';return Math.floor(n/86400)+'d'}
function fmtBytes(b){if(!b||b==='0')return'-';const n=parseInt(b);if(n<1024)return n+'B';if(n<1e6)return (n/1024).toFixed(1)+'K';return (n/1e6).toFixed(1)+'M'}
onMounted(load)
</script>

<style scoped>
.data-section { display:flex; flex-direction:column; gap:12px; }
.data-section h2 { font-size:15px; color:var(--fg); font-weight:600; }
.hint { font-size:11px; color:var(--fg3); }
.btn-refresh { padding:5px 14px; background:var(--bg3); color:var(--accent); border:1px solid var(--accent); border-radius:3px; cursor:pointer; font-size:11px; font-family:var(--font); width:fit-content; }
.btn-refresh:hover { background:var(--accent); color:#000; }
.btn-export { padding:5px 14px; background:var(--bg3); color:var(--fg2); border:1px solid var(--border); border-radius:3px; cursor:pointer; font-size:11px; font-family:var(--font); }
.table-wrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; background:var(--bg2); border:1px solid var(--border); border-radius:3px; font-size:11px; }
th,td { padding:5px 8px; text-align:left; border-bottom:1px solid var(--border); }
th { color:var(--fg3); font-weight:600; font-size:9px; text-transform:uppercase; letter-spacing:1px; background:var(--bg3); white-space:nowrap; }
.mono { font-family:var(--mono); font-size:10px; }
.cause { color:var(--fg3); font-size:10px; }
.empty { text-align:center; color:var(--fg3); padding:40px; font-size:12px; }
</style>
