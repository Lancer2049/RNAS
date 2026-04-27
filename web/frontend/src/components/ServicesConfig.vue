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
            <td>{{ val }}</td>
          </tr>
          <tr v-if="Object.keys(svc.data).length === 0">
            <td colspan="2" class="empty">Not configured</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const services = ref([
  { title: 'QoS / Traffic Control', data: {} },
  { title: 'VPN — IPsec', data: {} },
  { title: 'VPN — WireGuard', data: {} },
  { title: 'VPN — OpenVPN', data: {} },
  { title: 'Hotspot / Captive Portal', data: {} },
  { title: 'High Availability (VRRP)', data: {} },
])

async function loadServices() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    const cfg = data.config || {}

    const map = {
      qos: 0, 'vpn.d.ipsec': 1, 'vpn.d.wireguard': 2, 'vpn.d.openvpn': 3, hotspot: 4, ha: 5
    }
    for (const [key, val] of Object.entries(cfg)) {
      for (const [prefix, idx] of Object.entries(map)) {
        if (key.startsWith(prefix + '.')) {
          services.value[idx].data = { ...services.value[idx].data, ...val }
        }
      }
    }
  } catch (e) { console.error(e) }
}

onMounted(loadServices)
</script>

<style scoped>
.services-section { display: flex; flex-direction: column; gap: 16px; }
.section-header h2 { font-size: 18px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 15px; margin-bottom: 12px; color: #555; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { color: #888; font-weight: 600; text-transform: uppercase; font-size: 11px; }
.mono { font-family: monospace; font-size: 12px; }
.empty { text-align: center; color: #bbb; }
</style>
