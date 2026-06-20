<template>
  <div class="config-section">
    <div class="section-header">
      <h2>Configuration Editor</h2>
      <div class="header-actions">
        <select v-model="selectedModule" @change="loadModule">
          <option value="">Select module...</option>
          <option v-for="m in modules" :key="m" :value="m">{{ m }}</option>
        </select>
        <button class="btn-save" @click="saveConfig" :disabled="!selectedModule || saving">
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
        <button class="btn-apply" @click="applyConfig" :disabled="applying">
          {{ applying ? 'Applying...' : 'Apply Config' }}
        </button>
      </div>
    </div>

    <div v-if="selectedModule && currentValues" class="editor-card">
      <h3>{{ selectedModule }}</h3>
      <div class="field-row" v-for="(val, key) in currentValues" :key="key">
        <label>{{ key }}</label>
        <select v-if="isYesNo(val, key)" v-model="currentValues[key]" class="field-input">
          <option value="yes">yes</option><option value="no">no</option>
        </select>
        <input v-else-if="isPort(key)" v-model.number="currentValues[key]" type="number" min="1" max="65535" class="field-input" />
        <input v-else-if="isNumber(key)" v-model.number="currentValues[key]" type="number" class="field-input" />
        <input v-else v-model="currentValues[key]" :placeholder="val || '...'" class="field-input" />
        <span class="field-hint" v-if="isYesNo(val,key)||isPort(key)||isNumber(key)">{{ typeHint(val,key) }}</span>
      </div>
    </div>
    <div v-else-if="selectedModule" class="empty-state"><div class="icon">📝</div><div class="text">No data for {{ selectedModule }}</div></div>
    <div v-else class="empty-state"><div class="icon">📝</div><div class="text">Select a module to edit</div><div class="sub">Choose from {{ modules.length }} configuration sections</div></div>

    <div v-if="message" class="message" :class="messageType">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const modules = ref([])
const selectedModule = ref('')
const currentValues = ref(null)
const newKey = ref('')
const newVal = ref('')
const saving = ref(false)
const applying = ref(false)
const message = ref('')
const messageType = ref('success')

async function loadModules() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    modules.value = Object.keys(data.config || {})
  } catch (e) { console.error(e) }
}

async function loadModule() {
  if (!selectedModule.value) return
  try {
    const res = await fetch(`/api/config/${selectedModule.value.replace('.', '/')}`)
    const data = await res.json()
    const matches = data.config || {}
    currentValues.value = { ...matches[selectedModule.value] }
  } catch (e) { console.error(e) }
}

async function saveConfig() {
  saving.value = true
  try {
    const res = await fetch(`/api/config/${selectedModule.value.replace('.', '/')}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentValues.value)
    })
    if (res.ok) { message.value = 'Saved'; messageType.value = 'success' }
    else { message.value = 'Save failed'; messageType.value = 'error' }
  } catch (e) { message.value = 'Network error'; messageType.value = 'error' }
  saving.value = false
}

async function applyConfig() {
  applying.value = true
  await fetch('/api/config/apply', { method: 'POST' })
  applying.value = false
  message.value = 'Configuration applied'
  messageType.value = 'success'
}

function isYesNo(v,k){ return v==='yes'||v==='no'||k.includes('enabled')||k==='daemon'||k==='auth'||k.includes('check_') }
function isPort(k){ return k.includes('port') }
function isNumber(k){ return k.includes('timeout')||k.includes('interval')||k.includes('limit')||k.includes('count')||k.includes('thread')||k.includes('max')||k.includes('weight') }
function typeHint(v,k){ if(isYesNo(v,k))return 'yes/no'; if(isPort(k))return '1-65535'; if(isNumber(k))return 'number'; return '' }

function addField() {
  if (!newKey.value || !selectedModule.value) return
  if (!currentValues.value) currentValues.value = {}
  currentValues.value[newKey.value] = newVal.value
  newKey.value = ''
  newVal.value = ''
}

onMounted(loadModules)
</script>

<style scoped>
.config-section { display: flex; flex-direction: column; gap: 14px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.header-actions select { padding: 5px 10px; border: 1px solid var(--border); border-radius: 3px; background: var(--bg); color: var(--fg); font-size: 12px; font-family: var(--font); outline: none; }
.header-actions select:focus { border-color: var(--accent); }
.btn-save, .btn-apply, .btn-add { padding: 5px 14px; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.btn-save { background: var(--green); color: #000; }
.btn-apply { background: var(--accent); color: #000; }
.btn-add { background: var(--bg3); color: var(--accent); border: 1px solid var(--accent); }
.btn-add:hover { background: var(--accent); color: #000; }
.btn-save:disabled, .btn-apply:disabled { opacity: 0.4; }
.editor-card { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.editor-card h3 { font-size: 12px; color: var(--fg2); margin-bottom: 10px; font-family: var(--mono); text-transform: uppercase; letter-spacing: 1px; }
.field-row { display: grid; grid-template-columns: 200px 1fr; gap: 10px; margin-bottom: 8px; align-items: center; }
.field-row label { font-size: 11px; color: var(--fg3); font-family: var(--mono); }
.field-row input, .field-row select { padding: 4px 8px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; }
.field-row input:focus, .field-row select:focus { border-color: var(--accent); }
.field-hint { font-size: 10px; color: var(--fg3); }
.empty { text-align: center; color: var(--fg3); padding: 40px; font-size: 12px; }
.empty-state { text-align: center; padding: 40px; color: var(--fg3); }
.empty-state .icon { font-size: 36px; margin-bottom: 8px; }
.empty-state .text { font-size: 13px; color: var(--fg2); }
.empty-state .sub { font-size: 11px; }
.message { padding: 8px 14px; border-radius: 3px; font-size: 12px; }
.message.success { background: rgba(16,172,132,0.1); color: var(--green); border: 1px solid rgba(16,172,132,0.2); }
.message.error { background: rgba(238,82,83,0.1); color: var(--red); border: 1px solid rgba(238,82,83,0.2); }
</style>
