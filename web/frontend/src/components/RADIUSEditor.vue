<template>
  <div class="radius-editor">
    <div class="section-header">
      <h2>RADIUS Message Editor</h2>
    </div>

    <div class="editor-layout">
      <div class="build-panel">
        <h3>Build Request</h3>
        <div class="field-row">
          <label>Server</label>
          <input v-model="server" placeholder="192.168.0.202:1812" />
        </div>
        <div class="field-row">
          <label>Secret</label>
          <input v-model="secret" placeholder="testing123" />
        </div>
        <div class="field-row">
          <label>Type</label>
          <select v-model="portType">
            <option value="auth">Authentication (1812)</option>
            <option value="acct">Accounting (1813)</option>
            <option value="disconnect">CoA Disconnect (3799)</option>
          </select>
        </div>

        <h4>Attributes</h4>
        <div class="attr-row" v-for="(a, i) in attributes" :key="i">
          <select v-model="a.name" class="attr-name">
            <option value="">Select attribute...</option>
            <option v-for="d in dictAttrs" :key="d.name" :value="d.name">{{ d.vendor }}: {{ d.name }}</option>
          </select>
          <input v-model="a.value" placeholder="value" class="attr-value" />
          <button class="btn-remove" @click="attributes.splice(i, 1)">✕</button>
        </div>
        <button class="btn-add" @click="attributes.push({name:'', value:''})">+ Add Attribute</button>

        <button class="btn-send" @click="sendRequest" :disabled="sending || !attributes.length">
          {{ sending ? 'Sending...' : 'Send Request' }}
        </button>
      </div>

      <div class="response-panel">
        <h3>Response</h3>
        <div v-if="response" class="response-box">
          <div class="response-meta">
            <span class="badge" :class="responseType">{{ responseType.toUpperCase() }}</span>
            <span class="payload-hint">Attributes: {{ attributes.filter(a=>a.name).length }}</span>
          </div>
          <div class="response-raw">{{ response.output }}</div>
        </div>
        <div v-else class="empty-state">
          <div class="icon">🔧</div>
          <div class="text">Build and send a RADIUS request</div>
          <div class="sub">Select attributes from the dictionary and click Send</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const server = ref('192.168.0.202:1812')
const secret = ref('testing123')
const portType = ref('auth')
const attributes = reactive([{ name: 'User-Name', value: 'testuser' }, { name: 'User-Password', value: 'testpass' }])
const sending = ref(false)
const response = ref(null)
const responseType = ref('')
const payload = ref('')
const dictAttrs = ref([])

async function loadDict() {
  try {
    const res = await fetch('/api/dictionary')
    const data = await res.json()
    dictAttrs.value = Object.entries(data.attributes || {}).map(([name, info]) => ({ name, ...info }))
    dictAttrs.value.sort((a, b) => a.name.localeCompare(b.name))
  } catch {}
}

async function sendRequest() {
  sending.value = true
  try {
    const res = await fetch('/api/tools/radius-send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        server: server.value,
        secret: secret.value,
        type: portType.value,
        attributes: attributes.value.filter(a => a.name && a.value)
      })
    })
    const data = await res.json()
    response.value = data
    payload.value = data.payload || ''
    responseType.value = data.output?.includes('Access-Accept') ? 'accept' : data.output?.includes('Access-Reject') ? 'reject' : 'info'
  } catch (e) {
    response.value = { output: 'Request failed: ' + e.message }
    responseType.value = 'error'
  }
  sending.value = false
}

onMounted(loadDict)
</script>

<style scoped>
.radius-editor { display: flex; flex-direction: column; gap: 14px; }
.section-header h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.editor-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.build-panel, .response-panel { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.build-panel h3, .response-panel h3 { font-size: 12px; margin-bottom: 10px; color: var(--fg2); text-transform: uppercase; letter-spacing: 1px; }
.build-panel h4 { font-size: 11px; margin: 14px 0 8px; color: var(--fg3); }
.field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.field-row label { width: 60px; font-size: 11px; color: var(--fg3); flex-shrink: 0; }
.field-row input, .field-row select { flex: 1; padding: 4px 8px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; }
.field-row input:focus, .field-row select:focus { border-color: var(--accent); }
.attr-row { display: flex; gap: 4px; margin-bottom: 4px; }
.attr-name { flex: 2; padding: 4px 6px; border: 1px solid var(--border); border-radius: 3px; font-size: 11px; background: var(--bg); color: var(--fg); font-family: var(--font); }
.attr-value { flex: 1; padding: 4px 6px; border: 1px solid var(--border); border-radius: 3px; font-size: 11px; background: var(--bg); color: var(--fg); font-family: var(--font); }
.attr-name:focus, .attr-value:focus { border-color: var(--accent); outline: none; }
.btn-remove { padding: 2px 6px; background: rgba(238,82,83,0.08); border: 1px solid rgba(238,82,83,0.3); border-radius: 3px; cursor: pointer; font-size: 11px; color: var(--red); }
.btn-remove:hover { background: var(--red); color: #fff; }
.btn-add { margin-top: 8px; padding: 4px 12px; background: var(--bg3); border: 1px solid var(--accent); border-radius: 3px; cursor: pointer; font-size: 11px; color: var(--accent); font-family: var(--font); }
.btn-add:hover { background: var(--accent); color: #000; }
.btn-send { margin-top: 14px; width: 100%; padding: 8px; background: var(--accent); color: #000; border: none; border-radius: 3px; cursor: pointer; font-size: 12px; font-weight: 600; font-family: var(--font); }
.btn-send:disabled { opacity: 0.4; }
.response-box { margin-top: 8px; }
.response-meta { margin-bottom: 8px; display: flex; gap: 8px; align-items: center; }
.badge { padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: 600; }
.badge.accept { background: rgba(16,172,132,0.12); color: var(--green); }
.badge.reject { background: rgba(238,82,83,0.12); color: var(--red); }
.badge.info { background: rgba(10,189,227,0.12); color: var(--accent); }
.badge.error { background: rgba(255,159,67,0.12); color: #ff9f43; }
.payload-hint { font-size: 10px; color: var(--fg3); font-family: var(--mono); }
.response-raw { background: #0a0f14; color: var(--green); padding: 12px; border-radius: 3px; font-family: var(--mono); font-size: 11px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; border: 1px solid var(--border); }
.empty-state { text-align: center; padding: 40px; color: var(--fg3); }
.empty-state .icon { font-size: 36px; margin-bottom: 8px; }
.empty-state .text { font-size: 13px; margin-bottom: 4px; color: var(--fg2); }
.empty-state .sub { font-size: 11px; }
</style>
