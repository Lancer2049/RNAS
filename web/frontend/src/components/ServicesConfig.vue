<template>
  <div class="services-section">
    <div class="section-header"><h2>Services</h2></div>

    <div class="status-bar">
      <div class="status-item" v-for="s in vpnStatus" :key="s.name">
        <span class="s-icon">{{ s.icon }}</span>
        <span class="s-name">{{ s.name }}</span>
        <span class="s-state" :class="s.active?'on':'off'">{{ s.active ? 'UP' : 'DOWN' }}</span>
      </div>
    </div>

    <div class="svc-nav">
      <button v-for="svc in services" :key="svc.title" :class="{sel: activeSvc===svc.title}" @click="activeSvc=svc.title">
        {{ svc.title }}
      </button>
    </div>

    <template v-for="svc in services" :key="svc.title">
      <div v-if="activeSvc===svc.title" class="svc-panel">
        <div class="svc-header"><h3>{{ svc.title }}</h3></div>
        <div class="field-group">
          <div class="field-row" v-for="(val, key) in svc.data" :key="key">
            <label class="mono">{{ key }}</label>
            <select v-if="['yes','no','true','false'].includes(String(val).toLowerCase())" v-model="svc.data[key]" class="field-input">
              <option value="yes">yes</option><option value="no">no</option>
            </select>
            <input v-else v-model="svc.data[key]" class="field-input" />
          </div>
        </div>
        <div class="actions">
          <button class="btn-save" @click="saveSection(svc)" :disabled="svc.saving">{{ svc.saving ? '...' : 'Save' }}</button>
          <span v-if="svc.saved" class="saved-msg">✓ Saved</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const services = ref([
  { title: 'QoS / Traffic Control', data: {}, module: 'qos.global', saving: false, saved: false },
  { title: 'VPN - IPsec', data: {}, module: 'vpn.d.ipsec', saving: false, saved: false },
  { title: 'VPN - WireGuard', data: {}, module: 'vpn.d.wireguard', saving: false, saved: false },
  { title: 'VPN - OpenVPN', data: {}, module: 'vpn.d.openvpn', saving: false, saved: false },
  { title: 'Hotspot / Captive Portal', data: {}, module: 'hotspot.global', saving: false, saved: false },
  { title: 'High Availability (VRRP)', data: {}, module: 'ha.global', saving: false, saved: false },
])
const activeSvc = ref('QoS / Traffic Control')
const vpnStatus = ref([
  { name: 'IPsec', icon: '🔒', active: false },
  { name: 'WireGuard', icon: '🔐', active: false },
  { name: 'OpenVPN', icon: '🔑', active: false },
  { name: 'Hotspot', icon: '📡', active: false },
  { name: 'VRRP', icon: '⚡', active: false },
])

let servicesCache = null

async function loadAll() {
  if (!servicesCache) {
    const res = await fetch('/api/config')
    servicesCache = (await res.json()).config || {}
  }
  for (const s of services.value) {
    s.data = servicesCache[s.module] || {}
  }
}

async function saveSection(svc) {
  svc.saving = true; svc.saved = false
  await fetch(`/api/config/${svc.module.replace('.', '/')}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(svc.data)
  })
  svc.saving = false; svc.saved = true
}

onMounted(loadAll)
</script>

<style scoped>
.services-section { display: flex; flex-direction: column; gap: 14px; }
.section-header h2 { font-size: 15px; color: var(--fg); font-weight: 600; }
.status-bar { display: flex; gap: 10px; flex-wrap: wrap; }
.status-item { display: flex; align-items: center; gap: 6px; background: var(--bg2); padding: 6px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 11px; }
.s-icon { font-size: 12px; }
.s-name { font-weight: 600; color: var(--fg); }
.s-state { padding: 1px 6px; border-radius: 8px; font-size: 9px; font-weight: 600; }
.s-state.on { background: rgba(16,172,132,0.12); color: var(--green); }
.s-state.off { background: rgba(238,82,83,0.12); color: var(--red); }
.svc-nav { display: flex; gap: 4px; flex-wrap: wrap; }
.svc-nav button { padding: 5px 12px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--bg); color: var(--fg2); cursor: pointer; font-size: 11px; font-family: var(--font); }
.svc-nav button.sel { background: var(--accent); color: #000; border-color: var(--accent); }
.svc-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
.svc-header h3 { font-size: 13px; color: var(--fg); margin-bottom: 12px; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-row { display: flex; align-items: center; gap: 8px; }
.field-row label { width: 160px; font-size: 11px; color: var(--fg3); flex-shrink: 0; }
.field-input { flex: 1; padding: 5px 8px; border: 1px solid var(--border); border-radius: 3px; font-size: 11px; background: var(--bg); color: var(--fg); font-family: var(--mono); outline: none; }
.field-input:focus { border-color: var(--accent); }
.actions { margin-top: 12px; display: flex; align-items: center; gap: 8px; }
.btn-save { padding: 5px 14px; background: var(--green); color: #000; border: none; border-radius: var(--radius); cursor: pointer; font-size: 11px; font-family: var(--font); }
.btn-save:disabled { opacity: 0.4; }
.saved-msg { color: var(--green); font-size: 11px; }
</style>
