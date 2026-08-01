<template>
  <div class="cert-page">
    <h2>Certificate Manager</h2>
    <p class="hint">SSL/TLS certificates for SSTP, HTTPS, OpenVPN</p>
    <div class="cert-actions"><button class="btn" @click="showGen=true">+ Generate Self-Signed</button></div>

    <div v-if="showGen" class="gen-form">
      <input v-model="genName" placeholder="Name (e.g. server)" />
      <input v-model="genCN" placeholder="Common Name (e.g. RNAS Server)" />
      <input v-model.number="genDays" type="number" placeholder="Days" />
      <button class="btn btn-accent" @click="generate">Generate</button>
      <button class="btn" @click="showGen=false">Cancel</button>
    </div>

    <table v-if="certs.length">
      <thead><tr><th>Name</th><th>Type</th><th>Size</th><th>Modified</th></tr></thead>
      <tbody>
        <tr v-for="c in certs" :key="c.name">
          <td class="mono">{{ c.name }}</td><td>{{ c.kind }}</td><td>{{ (c.size/1024).toFixed(1) }}KB</td><td>{{ new Date(c.modified*1000).toLocaleDateString() }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No certificates found</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const certs = ref([]), showGen = ref(false)
const genName = ref('server'), genCN = ref('RNAS Server'), genDays = ref(3650)

async function load() { try { const r=await fetch('/api/system/certificates'); certs.value=(await r.json()).certificates||[] } catch {} }
async function generate() {
  if (!genName.value.trim() || !genDays.value || genDays.value < 1) { alert('Name and days (>=1) are required'); return }
  try {
    const r = await fetch('/api/system/certificates/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:genName.value.trim(),cn:genCN.value,days:genDays.value})})
    if (!r.ok) { const d = await r.json().catch(()=>({})); alert('Generate failed: ' + (d.detail || r.status)); return }
    showGen.value=false; load()
  } catch(e) { alert('Generate error: ' + e.message) }
}
onMounted(load)
</script>

<style scoped>
.cert-page{display:flex;flex-direction:column;gap:12px}
h2{font-size:15px;color:var(--fg);font-weight:600}
.hint{font-size:11px;color:var(--fg3)}
.cert-actions{display:flex;gap:8px}
.gen-form{display:flex;gap:6px;flex-wrap:wrap;background:var(--bg2);padding:12px;border:1px solid var(--border);border-radius:3px}
.gen-form input{padding:5px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--mono);flex:1;min-width:100px}
table{width:100%;border-collapse:collapse;background:var(--bg2);border:1px solid var(--border);font-size:11px}
th,td{padding:5px 8px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--fg3);font-size:9px;text-transform:uppercase;letter-spacing:1px;background:var(--bg3)}
.mono{font-family:var(--mono)}
.empty{text-align:center;color:var(--fg3);padding:24px}
</style>
