<template>
  <div class="services-section">
    <div class="section-header"><h2>Services</h2></div>

    <div class="status-bar">
      <div class="status-item" v-for="s in vpnStatus" :key="s.name">
        <span class="s-icon">{{ s.icon }}</span>
        <span class="s-name">{{ s.name }}</span>
        <span class="s-state" :class="s.active?'on':'off'">{{ s.active ? 'UP' : 'DOWN' }}</span>
        <span class="s-detail" v-if="s.detail">{{ s.detail }}</span>
      </div>
    </div>

    <div class="card" v-for="svc in services" :key="svc.title">
      <h3>{{ svc.title }}</h3>
      <table>
        <thead><tr><th>Key</th><th>Value</th></tr></thead>
        <tbody>
          <tr v-for="(val, key) in svc.data" :key="key">
            <td class="mono">{{ key }}</td>
            <td><input v-model="svc.data[key]" @blur="saveSection(svc)" /></td>
          </tr>
          <tr v-if="Object.keys(svc.data).length === 0">
            <td colspan="2" class="empty">Not configured</td>
          </tr>
        </tbody>
      </table>
      <div class="actions">
        <button class="btn-save" @click="saveSection(svc)" :disabled="svc.saving">{{ svc.saving ? '...' : 'Save' }}</button>
        <span v-if="svc.saved" class="saved-msg">✓ Saved</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const services = ref([
  { title: 'QoS / Traffic Control', data: {}, module: 'qos.global', saving: false, saved: false },
  { title: 'VPN — IPsec', data: {}, module: 'vpn.d.ipsec.global', saving: false, saved: false },
  { title: 'VPN — WireGuard', data: {}, module: 'vpn.d.wireguard.global', saving: false, saved: false },
  { title: 'VPN — OpenVPN', data: {}, module: 'vpn.d.openvpn.global', saving: false, saved: false },
  { title: 'Hotspot / Captive Portal', data: {}, module: 'hotspot.global', saving: false, saved: false },
  { title: 'High Availability (VRRP)', data: {}, module: 'ha.global', saving: false, saved: false },
])

async function loadAll() {
  const res = await fetch('/api/config')
  const cfg = (await res.json()).config || {}
  for (const s of services.value) {
    s.data = cfg[s.module] || {}
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
.status-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }
.status-item { display: flex; align-items: center; gap: 6px; background: var(--bg2); padding: 6px 12px; border: 1px solid var(--border); border-radius: 3px; font-size: 11px; }
.s-icon { font-size: 12px; }
.s-name { font-weight: 600; color: var(--fg); }
.s-state { padding: 1px 6px; border-radius: 8px; font-size: 9px; font-weight: 600; }
.s-state.on { background: rgba(16,172,132,0.12); color: var(--green); }
.s-state.off { background: rgba(238,82,83,0.12); color: var(--red); }
.s-detail { color: var(--fg3); }
.card { background: var(--bg2); padding: 14px; border: 1px solid var(--border); border-radius: 3px; }
.card h3 { font-size: 12px; margin-bottom: 8px; color: var(--fg2); text-transform: uppercase; letter-spacing: 1px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 5px 10px; text-align: left; border-bottom: 1px solid var(--border); font-size: 12px; }
th { color: var(--fg3); font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 1px; }
.mono { font-family: var(--mono); font-size: 11px; }
td input { width: 100%; padding: 4px 8px; border: 1px solid var(--border); border-radius: 3px; font-size: 12px; background: var(--bg); color: var(--fg); font-family: var(--font); outline: none; }
td input:focus { border-color: var(--accent); }
.empty { text-align: center; color: var(--fg3); font-size: 12px; }
.actions { margin-top: 10px; display: flex; align-items: center; gap: 8px; }
.btn-save { padding: 5px 14px; background: var(--green); color: #000; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; font-family: var(--font); }
.btn-save:disabled { opacity: 0.4; }
.saved-msg { color: var(--green); font-size: 11px; }
</style>
