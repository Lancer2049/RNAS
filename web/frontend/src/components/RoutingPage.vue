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
.routing-section { display:flex; flex-direction:column; gap:12px; } h2{font-size:15px;color:var(--fg);font-weight:600;} .hint{font-size:11px;color:var(--fg3);}
.tab-bar { display:flex; gap:8px; align-items:center; background:var(--bg2); padding:8px 14px; border-radius:3px; border:1px solid var(--border); }
.tab-bar button { padding:5px 14px; border:1px solid var(--border); border-radius:3px; background:var(--bg); color:var(--fg2); cursor:pointer; font-size:12px; font-family:var(--font); }
.tab-bar button.active { background:var(--accent); color:#000; border-color:var(--accent); }
.refresh { margin-left:auto; color:var(--accent); cursor:pointer; font-size:12px; }
.refresh:hover { text-decoration: underline; }
.tab-content { background:var(--bg2); padding:14px; border:1px solid var(--border); border-radius:3px; }
table { width:100%; border-collapse:collapse; font-size:12px; }
th,td { padding:5px 10px; text-align:left; border-bottom:1px solid var(--border); } th{color:var(--fg3);font-size:10px;text-transform:uppercase;letter-spacing:1px;}
.mono { font-family:var(--mono); font-size:11px; }
.state { padding:2px 8px; border-radius:3px; font-size:10px; font-weight:600; }
.state.Full,.state.Established { background:rgba(16,172,132,0.12); color:var(--green); }
.state.ExStart,.state.Active { background:rgba(255,159,67,0.12); color:#ff9f43; }
.state.Down,.state.Idle { background:rgba(238,82,83,0.12); color:var(--red); }
.empty { text-align:center; color:var(--fg3); padding:20px; font-size:12px; }
</style>
