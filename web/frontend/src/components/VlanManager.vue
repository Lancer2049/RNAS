<template>
  <div class="vlan-section">
    <h2>VLAN per User</h2>
    <p class="hint">accel-ppp vlan-mon: assign VLAN by RADIUS Tunnel-Private-Group-Id</p>

    <div class="status-row">
      <span class="label">vlan-mon module:</span>
      <span :class="'value '+vlanStatus.module">{{ vlanStatus.module || 'unknown' }}</span>
      <span class="label">kernel 8021q:</span>
      <span :class="'value '+vlanStatus.kernel">{{ vlanStatus.kernel || 'unknown' }}</span>
    </div>

    <h3>Active VLAN Interfaces</h3>
    <table v-if="vlanStatus.interfaces?.length">
      <thead><tr><th>Interface</th><th>VLAN ID</th><th>State</th><th>Parent</th></tr></thead>
      <tbody>
        <tr v-for="v in vlanStatus.interfaces" :key="v.name">
          <td class="mono">{{ v.name }}</td><td>VLAN {{ v.id }}</td>
          <td><span :class="{up: v.up}">{{ v.up ? 'UP' : 'DOWN' }}</span></td>
          <td>{{ v.parent }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No active VLAN interfaces — requires physical NIC with 802.1Q support</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const vlanStatus = ref({ module: '', kernel: '', interfaces: [] })
async function fetchVlans() {
  try { const r = await fetch('/api/vlans'); vlanStatus.value = await r.json() } catch {}
}
onMounted(fetchVlans)
</script>

<style scoped>
.vlan-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:18px;} h3{font-size:15px;margin:0;} .hint{font-size:13px;color:#888;}
.status-row { display:flex; gap:16px; align-items:center; background:#fff; padding:12px 16px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
.label { font-size:13px; color:#666; }
.value { font-size:13px; font-weight:600; padding:2px 8px; border-radius:4px; color:#16a34a; background:#dcfce7; }
.value.missing { color:#dc2626; background:#fef2f2; }
table { width:100%; border-collapse:collapse; font-size:13px; background:#fff; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
th,td { padding:6px 10px; text-align:left; border-bottom:1px solid #eee; } th{color:#666;font-size:11px;text-transform:uppercase;}
.mono { font-family:monospace; } .up { color:#16a34a; font-weight:600; }
.empty { text-align:center; color:#999; padding:40px; background:#fff; border-radius:8px; }
</style>
