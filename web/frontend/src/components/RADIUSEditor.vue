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
            <span class="badge" :class="responseType">{{ responseType }}</span>
            <span class="payload-hint">{{ payload }}</span>
          </div>
          <pre class="response-text">{{ response.output }}</pre>
        </div>
        <div v-else class="empty">Send a request to see the response</div>
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
.radius-editor { display: flex; flex-direction: column; gap: 16px; }
.section-header h2 { font-size: 18px; }
.editor-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.build-panel, .response-panel { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.build-panel h3, .response-panel h3 { font-size: 15px; margin-bottom: 12px; color: #555; }
.build-panel h4 { font-size: 13px; margin: 16px 0 8px; color: #666; }

.field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.field-row label { width: 60px; font-size: 13px; color: #666; flex-shrink: 0; }
.field-row input, .field-row select { flex: 1; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }

.attr-row { display: flex; gap: 4px; margin-bottom: 4px; }
.attr-name { flex: 2; padding: 4px 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px; }
.attr-value { flex: 1; padding: 4px 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px; }
.btn-remove { padding: 2px 6px; background: #fee; border: 1px solid #fcc; border-radius: 3px; cursor: pointer; font-size: 12px; color: #c33; }

.btn-add { margin-top: 8px; padding: 4px 12px; background: #f0f4ff; border: 1px solid #c4d4f6; border-radius: 4px; cursor: pointer; font-size: 12px; color: #3b82f6; }
.btn-send { margin-top: 16px; width: 100%; padding: 10px; background: #3b82f6; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-send:disabled { opacity: 0.5; }

.response-box { margin-top: 8px; }
.response-meta { margin-bottom: 8px; display: flex; gap: 8px; align-items: center; }
.badge { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.badge.accept { background: #dcfce7; color: #166534; }
.badge.reject { background: #fee2e2; color: #991b1b; }
.badge.info { background: #dbeafe; color: #1e40af; }
.badge.error { background: #fef3c7; color: #92400e; }
.payload-hint { font-size: 11px; color: #999; font-family: monospace; }
.response-text { background: #f8f9fa; padding: 12px; border-radius: 4px; font-size: 12px; font-family: monospace; white-space: pre-wrap; max-height: 400px; overflow-y: auto; border: 1px solid #eee; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
