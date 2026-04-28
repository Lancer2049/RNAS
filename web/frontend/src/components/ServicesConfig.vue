<template>
  <div class="services-section">
    <div class="section-header"><h2>Services Configuration</h2></div>

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
.services-section { display: flex; flex-direction: column; gap: 16px; }
.section-header h2 { font-size: 18px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 15px; margin-bottom: 8px; color: #555; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 6px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { color: #888; font-weight: 600; text-transform: uppercase; font-size: 11px; }
.mono { font-family: monospace; font-size: 12px; }
td input { width: 100%; padding: 4px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 13px; }
td input:focus { border-color: #3b82f6; outline: none; }
.empty { text-align: center; color: #bbb; }
.actions { margin-top: 12px; display: flex; align-items: center; gap: 8px; }
.btn-save { padding: 6px 16px; background: #22c55e; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.saved-msg { color: #22c55e; font-size: 13px; }
</style>
