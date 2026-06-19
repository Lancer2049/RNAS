<template>
  <div class="routing-section">
    <h2>Dynamic Routing</h2>
    <p class="hint">OSPF / BGP status from FRRouting via vtysh</p>

    <div class="tab-bar">
      <button :class="{active:tab==='ospf'}" @click="tab='ospf'">OSPF</button>
      <button :class="{active:tab==='bgp'}" @click="tab='bgp'">BGP</button>
      <button :class="{active:tab==='routes'}" @click="tab='routes'">Route Table</button>
      <span class="refresh" @click="fetchAll">🔄 Refresh</span>
    </div>

    <!-- OSPF Tab -->
    <div v-if="tab==='ospf'" class="tab-content">
      <h3>OSPF Neighbors</h3>
      <table v-if="ospf.neighbors">
        <thead><tr><th>Neighbor ID</th><th>State</th><th>Address</th><th>Interface</th></tr></thead>
        <tbody>
          <tr v-for="n in ospf.neighbors" :key="n.id">
            <td class="mono">{{ n.id }}</td>
            <td><span :class="'state '+n.state">{{ n.state }}</span></td>
            <td class="mono">{{ n.address }}</td><td>{{ n.iface }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">No OSPF neighbors</div>
    </div>

    <!-- BGP Tab -->
    <div v-if="tab==='bgp'" class="tab-content">
      <h3>BGP Peers</h3>
      <table v-if="bgp.peers">
        <thead><tr><th>Peer</th><th>AS</th><th>State</th><th>Uptime</th><th>RCV</th><th>SENT</th></tr></thead>
        <tbody>
          <tr v-for="p in bgp.peers" :key="p.peer">
            <td class="mono">{{ p.peer }}</td><td>{{ p.as }}</td>
            <td><span :class="'state '+p.state">{{ p.state }}</span></td>
            <td>{{ p.uptime }}</td><td>{{ p.rcv }}</td><td>{{ p.sent }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">No BGP peers</div>
    </div>

    <!-- Route Table Tab -->
    <div v-if="tab==='routes'" class="tab-content">
      <h3>Routing Table</h3>
      <table v-if="bgp.routes">
        <thead><tr><th>Network</th><th>Next Hop</th><th>Protocol</th></tr></thead>
        <tbody>
          <tr v-for="(r,i) in bgp.routes" :key="i">
            <td class="mono">{{ r.network }}</td><td class="mono">{{ r.nexthop }}</td><td>{{ r.proto }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const tab = ref('ospf')
const ospf = ref({ neighbors: [] })
const bgp = ref({ peers: [], routes: [] })

async function fetchAll() {
  try {
    const r = await fetch('/api/routing/status')
    const d = await r.json()
    ospf.value = d.ospf || { neighbors: [] }
    bgp.value = d.bgp || { peers: [], routes: [] }
  } catch {}
}
onMounted(fetchAll)
</script>

<style scoped>
.routing-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:18px;} .hint{font-size:13px;color:#888;}
.tab-bar { display:flex; gap:8px; align-items:center; background:#fff; padding:8px 16px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
.tab-bar button { padding:6px 16px; border:1px solid #ddd; border-radius:6px; background:#fff; cursor:pointer; font-size:13px; }
.tab-bar button.active { background:#3b82f6; color:#fff; border-color:#3b82f6; }
.refresh { margin-left:auto; color:#3b82f6; cursor:pointer; font-size:13px; }
.tab-content { background:#fff; padding:16px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }
table { width:100%; border-collapse:collapse; font-size:13px; }
th,td { padding:6px 10px; text-align:left; border-bottom:1px solid #eee; } th{color:#666;font-size:11px;text-transform:uppercase;}
.mono { font-family:monospace; font-size:12px; }
.state { padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
.state.Full,.state.Established { background:#dcfce7; color:#16a34a; }
.state.ExStart,.state.Active { background:#fef9c3; color:#ca8a04; }
.state.Down,.state.Idle { background:#fef2f2; color:#dc2626; }
.empty { text-align:center; color:#999; padding:20px; }
</style>
