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
.hotspot-section{display:flex;flex-direction:column;gap:12px}h2{font-size:18px}.hint{font-size:13px;color:#888}
.stats{display:flex;gap:16px;background:#fff;padding:12px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08);flex-wrap:wrap}
.stat{display:flex;flex-direction:column;gap:4px}.label{font-size:11px;color:#888;text-transform:uppercase}
.value{font-size:14px;font-weight:600}.value.Active{color:#16a34a}.value.Inactive{color:#dc2626}
.test-box,.url-box{background:#fff;padding:16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
h3{font-size:15px;margin:0 0 8px}.test-row{display:flex;gap:8px;align-items:center}
input{padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px;width:140px}
button{padding:8px 16px;background:#3b82f6;color:#fff;border:none;border-radius:6px;cursor:pointer}
.result{font-size:13px;font-weight:600}.result.ok{color:#16a34a}.result.fail{color:#dc2626}
code{background:#f1f5f9;padding:4px 8px;border-radius:4px;font-size:13px}.note{font-size:12px;color:#888;margin:4px 0 0}
</style>
