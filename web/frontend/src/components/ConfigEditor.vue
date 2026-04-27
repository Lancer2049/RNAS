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
        <input v-model="currentValues[key]" :placeholder="val || '...'" />
      </div>
      <div class="field-row new-field">
        <input v-model="newKey" placeholder="new key" />
        <input v-model="newVal" placeholder="value" />
        <button class="btn-add" @click="addField" :disabled="!newKey">Add</button>
      </div>
    </div>
    <div v-else-if="selectedModule" class="empty">No config data loaded</div>
    <div v-else class="empty">Select a module to edit</div>

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
  try {
    const res = await fetch('/api/config/apply', { method: 'POST' })
    if (res.ok) { message.value = 'Config applied — services reloaded'; messageType.value = 'success' }
    else { message.value = 'Apply failed'; messageType.value = 'error' }
  } catch (e) { message.value = 'Network error'; messageType.value = 'error' }
  applying.value = false
}

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
.config-section { display: flex; flex-direction: column; gap: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 18px; }
.header-actions { display: flex; gap: 8px; }
.header-actions select { padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; }
.btn-save, .btn-apply, .btn-add { padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-save { background: #22c55e; color: #fff; }
.btn-apply { background: #3b82f6; color: #fff; }
.btn-add { background: #8b5cf6; color: #fff; }
.btn-save:disabled, .btn-apply:disabled { opacity: 0.5; }
.editor-card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.editor-card h3 { font-size: 14px; color: #555; margin-bottom: 12px; font-family: monospace; }
.field-row { display: grid; grid-template-columns: 200px 1fr; gap: 12px; margin-bottom: 8px; align-items: center; }
.field-row label { font-size: 13px; color: #888; font-family: monospace; }
.field-row input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.new-field { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #eee; grid-template-columns: 1fr 1fr auto; }
.new-field label { display: none; }
.empty { text-align: center; color: #bbb; padding: 40px; font-size: 14px; }
.message { padding: 10px 16px; border-radius: 4px; font-size: 13px; }
.message.success { background: #dcfce7; color: #166534; }
.message.error { background: #fee2e2; color: #991b1b; }
</style>
