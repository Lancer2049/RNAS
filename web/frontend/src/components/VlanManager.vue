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
.vlan-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600} h3{font-size:12px;color:var(--fg2);text-transform:uppercase;letter-spacing:1px} .hint{font-size:11px;color:var(--fg3)}
.status-row { display:flex; gap:14px; align-items:center; background:var(--bg2); padding:10px 14px; border:1px solid var(--border); border-radius:3px }
.label { font-size:11px; color:var(--fg3) }
.value { font-size:12px; font-weight:600; padding:2px 8px; border-radius:3px; color:var(--green); background:rgba(16,172,132,0.12) }
.value.missing { color:var(--red); background:rgba(238,82,83,0.12) }
table { width:100%; border-collapse:collapse; font-size:12px; background:var(--bg2); border:1px solid var(--border); border-radius:3px }
th,td { padding:5px 10px; text-align:left; border-bottom:1px solid var(--border) } th{color:var(--fg3);font-size:10px;text-transform:uppercase;letter-spacing:1px}
.mono { font-family:var(--mono) } .up { color:var(--green); font-weight:600 }
.empty { text-align:center; color:var(--fg3); padding:40px; font-size:12px; background:var(--bg2); border:1px solid var(--border); border-radius:3px }
</style>
