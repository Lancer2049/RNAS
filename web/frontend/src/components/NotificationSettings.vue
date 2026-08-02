<template>
  <div class="notif-page">
    <div class="nh">
      <h2>🔔 Notification Settings</h2>
      <p class="hint">Send health alerts to Telegram or a generic webhook when services fail, disk fills up, or sessions misbehave.</p>
    </div>

    <div class="nf-form">
      <label class="nf-toggle">
        <input type="checkbox" v-model="cfg.enabled" class="nf-enabled" />
        <span>Enable alert notifications</span>
      </label>

      <div class="field">
        <label>Telegram Bot Token</label>
        <input v-model="cfg.telegram_bot_token" placeholder="123456:ABC-DEF..." />
      </div>
      <div class="field">
        <label>Telegram Chat ID</label>
        <input v-model="cfg.telegram_chat_id" placeholder="-1001234567890" />
      </div>
      <div class="field">
        <label>Webhook URL</label>
        <input v-model="cfg.webhook_url" placeholder="https://example.com/hook" />
      </div>

      <div class="nf-actions">
        <button class="btn-save" @click="save" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button class="btn-test" @click="test" :disabled="testing">{{ testing ? 'Testing...' : 'Send Test' }}</button>
      </div>

      <div v-if="msg" class="nf-msg" :class="msgType">{{ msg }}</div>
      <div v-if="results.length" class="nf-results">
        <div v-for="r in results" :key="r.channel" class="nf-result" :class="r.ok ? 'ok' : 'err'">
          {{ r.channel }}: {{ r.ok ? 'delivered' : 'failed' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const cfg = ref({ enabled: false, telegram_bot_token: '', telegram_chat_id: '', webhook_url: '' })
const saving = ref(false)
const testing = ref(false)
const msg = ref('')
const msgType = ref('')
const results = ref([])

onMounted(async () => {
  try {
    const r = await fetch('/api/system/notifications')
    cfg.value = { ...cfg.value, ...(await r.json()) }
  } catch {}
})

async function save() {
  saving.value = true; msg.value = ''; results.value = []
  try {
    const r = await fetch('/api/system/notifications', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg.value) })
    if (!r.ok) throw new Error(r.status)
    msg.value = 'Notification settings saved'; msgType.value = 'ok'
  } catch (e) { msg.value = 'Save failed: ' + e.message; msgType.value = 'err' }
  saving.value = false
}

async function test() {
  testing.value = true; msg.value = ''; results.value = []
  try {
    const r = await fetch('/api/system/notifications/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg.value) })
    const d = await r.json()
    results.value = d.results || []
    if (!r.ok) throw new Error(r.status)
  } catch (e) { msg.value = 'Test failed: ' + e.message; msgType.value = 'err' }
  testing.value = false
}
</script>

<style scoped>
.notif-page{display:flex;flex-direction:column;gap:16px;max-width:640px;margin:0 auto}
.nh h2{font-size:18px;color:var(--fg);font-weight:700}
.hint{font-size:12px;color:var(--fg3);margin-top:4px}
.nf-form{background:var(--bg2);padding:20px;border:1px solid var(--border);border-radius:4px;display:flex;flex-direction:column;gap:14px}
.nf-toggle{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--fg);cursor:pointer}
.nf-toggle input{width:16px;height:16px;accent-color:var(--green)}
.field{display:flex;flex-direction:column;gap:4px}
.field label{font-size:10px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px}
.field input{padding:8px 12px;border:1px solid var(--border);border-radius:3px;font-size:13px;background:var(--bg);color:var(--fg);font-family:var(--mono);outline:none}
.field input:focus{border-color:var(--accent)}
.nf-actions{display:flex;gap:8px;margin-top:4px}
.btn-save,.btn-test{padding:8px 20px;border-radius:3px;cursor:pointer;font-size:12px;font-weight:600;font-family:var(--font);border:none}
.btn-save{background:var(--green);color:#000}
.btn-test{background:var(--bg3);color:var(--fg2)}
.btn-save:disabled,.btn-test:disabled{opacity:0.4}
.nf-msg{padding:10px;border-radius:3px;font-size:12px;text-align:center}
.nf-msg.ok{background:rgba(16,172,132,0.1);color:var(--green)}
.nf-msg.err{background:rgba(238,82,83,0.1);color:var(--red)}
.nf-results{display:flex;flex-direction:column;gap:6px}
.nf-result{padding:8px 12px;border-radius:3px;font-size:12px}
.nf-result.ok{background:rgba(16,172,132,0.1);color:var(--green)}
.nf-result.err{background:rgba(238,82,83,0.1);color:var(--red)}
</style>
