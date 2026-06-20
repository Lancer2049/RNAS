<template>
  <div class="hotspot-section">
    <h2>Captive Portal</h2>
    <p class="hint">Hotspot login page + RADIUS-backed authentication + iptables redirect</p>

    <div class="stats">
      <div class="stat"><span class="label">Portal Page</span><span class="value" :class="status.portal">{{ status.portal || 'N/A' }}</span></div>
      <div class="stat"><span class="label">RADIUS Auth</span><span class="value" :class="status.auth">{{ status.auth || 'N/A' }}</span></div>
      <div class="stat"><span class="label">iptables Redirect</span><span class="value" :class="status.iptables">{{ status.iptables || 'N/A' }}</span></div>
    </div>

    <div class="test-box">
      <h3>Test Authentication</h3>
      <div class="test-row">
        <input v-model="testUser" placeholder="Username" />
        <input v-model="testPass" type="password" placeholder="Password" />
        <button @click="testLogin">{{ testing ? '...' : 'Test Login' }}</button>
        <span :class="'result '+(loginOk?'ok':'fail')" v-if="loginResult">{{ loginResult }}</span>
      </div>
    </div>

    <div class="url-box">
      <h3>Portal URL</h3>
      <code>http://192.168.0.203:8099/hotspot</code>
      <p class="note">Clients on 192.168.100.0/24 are auto-redirected</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const status = ref({ portal: '', auth: '', iptables: '' })
const testUser = ref('testuser'), testPass = ref('testpass')
const testing = ref(false), loginResult = ref(''), loginOk = ref(false)

onMounted(async()=>{
  try { const r=await fetch('/api/hotspot/status'); status.value=await r.json() } catch {}
})

async function testLogin() {
  testing.value=true; loginResult.value=''
  try {
    const r=await fetch('/hotspot/login', {method:'POST',body:new URLSearchParams({username:testUser.value,password:testPass.value})})
    const txt=await r.text()
    loginOk.value=txt==='Authenticated'
    loginResult.value=loginOk.value?'Authenticated ✅':'Access Denied ❌'
  } catch { loginResult.value='Error' }
  testing.value=false
}
</script>

<style scoped>
.hotspot-section{display:flex;flex-direction:column;gap:12px}h2{font-size:15px;color:var(--fg);font-weight:600}.hint{font-size:11px;color:var(--fg3)}
.stats{display:flex;gap:16px;background:var(--bg2);padding:12px 14px;border:1px solid var(--border);border-radius:3px;flex-wrap:wrap}
.stat{display:flex;flex-direction:column;gap:4px}.label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.value{font-size:14px;font-weight:600}.value.Active{color:var(--green)}.value.Inactive{color:var(--red)}
.test-box,.url-box{background:var(--bg2);padding:14px;border:1px solid var(--border);border-radius:3px}
h3{font-size:12px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.test-row{display:flex;gap:8px;align-items:center}
input{padding:6px 10px;border:1px solid var(--border);border-radius:3px;font-size:12px;width:140px;background:var(--bg);color:var(--fg);font-family:var(--font);outline:none}
input:focus{border-color:var(--accent)}
button{padding:6px 14px;background:var(--bg3);color:var(--accent);border:1px solid var(--accent);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
button:hover{background:var(--accent);color:#000}
.result{font-size:12px;font-weight:600}.result.ok{color:var(--green)}.result.fail{color:var(--red)}
code{background:var(--bg3);padding:4px 8px;border-radius:3px;font-size:12px;color:var(--accent);font-family:var(--mono)}
.note{font-size:10px;color:var(--fg3);margin:4px 0 0}
</style>
