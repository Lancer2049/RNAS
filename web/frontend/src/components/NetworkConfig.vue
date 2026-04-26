<template>
  <div class="network-section">
    <div class="section-header">
      <h2>Network Configuration</h2>
    </div>

    <div class="card">
      <h3>Interfaces</h3>
      <table>
        <thead><tr><th>Name</th><th>Type</th><th>Device</th><th>IP / Mode</th></tr></thead>
        <tbody>
          <tr v-for="(iface, key) in interfaces" :key="key">
            <td>{{ key }}</td>
            <td>{{ iface.device ? 'Interface' : 'Device' }}</td>
            <td>{{ iface.device || '-' }}</td>
            <td>{{ iface.proto === 'static' ? iface.ipaddr + '/' + iface.netmask : iface.proto || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>DHCP Server</h3>
      <table>
        <thead><tr><th>Interface</th><th>Range Start</th><th>Limit</th><th>Lease Time</th></tr></thead>
        <tbody>
          <tr v-for="(dhcp, key) in dhcpConfigs" :key="key">
            <td>{{ key }}</td>
            <td>{{ dhcp.start }}</td>
            <td>{{ dhcp.limit }}</td>
            <td>{{ dhcp.leasetime }}</td>
          </tr>
          <tr v-if="Object.keys(dhcpConfigs).length === 0">
            <td colspan="4" class="empty">No DHCP scopes configured</td>
          </tr>
        </tbody>
      </table>
      <div class="dns-section" v-if="dnsList">
        <strong>DNS:</strong> {{ dnsList }}
      </div>
    </div>

    <div class="card">
      <h3>Firewall Zones</h3>
      <table>
        <thead><tr><th>Zone</th><th>Input</th><th>Output</th><th>Forward</th><th>Networks</th></tr></thead>
        <tbody>
          <tr v-for="(zone, key) in firewallZones" :key="key">
            <td>{{ key }}</td>
            <td>{{ zone.input }}</td>
            <td>{{ zone.output }}</td>
            <td>{{ zone.forward }}</td>
            <td>{{ zone.networks }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const interfaces = ref({})
const dhcpConfigs = ref({})
const dnsList = ref('')
const firewallZones = ref({})

async function loadNetwork() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    const cfg = data.config || {}

    for (const [key, val] of Object.entries(cfg)) {
      if (key.startsWith('network.d.interface/')) {
        const name = key.replace('network.d.interface/', '')
        interfaces.value[name] = val
      } else if (key.startsWith('network.d.device/')) {
        const name = key.replace('network.d.device/', '')
        interfaces.value[name] = val
      } else if (key.startsWith('network.d.dhcp/dhcp ')) {
        dhcpConfigs.value[key.replace('network.d.dhcp/dhcp ', '')] = val
      } else if (key.startsWith('network.d.dhcp/dhcp_option dns')) {
        dnsList.value = val.list || ''
      } else if (key.startsWith('network.d.zone/')) {
        firewallZones.value[key.replace('network.d.zone/', '')] = val
      }
    }
  } catch (e) {
    console.error('Network config error:', e)
  }
}

onMounted(loadNetwork)
</script>

<style scoped>
.network-section { display: flex; flex-direction: column; gap: 16px; }
.section-header h2 { font-size: 18px; margin-bottom: 8px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { font-size: 15px; margin-bottom: 12px; color: #555; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 13px; }
th { color: #888; font-weight: 600; text-transform: uppercase; font-size: 11px; }
.empty { text-align: center; color: #bbb; }
.dns-section { margin-top: 12px; font-size: 13px; color: #555; }
</style>
