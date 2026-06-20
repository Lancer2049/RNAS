<template>
  <div class="ros-ip">
    <div class="ros-tabs">
      <button v-for="t in tabs" :key="t.id" :class="{sel: tab===t.id}" @click="tab=t.id; t.id==='arp'?fetchArp():t.id==='fw'?fetchFW():t.id==='dhcp'?fetchDHCP():fetchRoutes()">
        {{ t.label }} <span v-if="t.count" class="ct">{{ t.count }}</span>
      </button>
    </div>

    <!-- ARP Table -->
    <div v-if="tab==='arp'" class="tab-body">
      <table>
        <thead><tr><th>IP Address</th><th>MAC Address</th><th>Interface</th><th>State</th></tr></thead>
        <tbody>
          <tr v-for="a in arp" :key="a.ip">
            <td class="mono">{{ a.ip }}</td><td class="mono">{{ a.mac }}</td><td>{{ a.dev }}</td>
            <td><span :class="'tag '+(a.state.toLowerCase())">{{ a.state }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Firewall -->
    <div v-if="tab==='fw'" class="tab-body">
      <div v-for="c in fwChains" :key="c.name" class="fw-chain">
        <h3>{{ c.name }}</h3>
        <div v-for="(r,i) in c.rules" :key="i" class="fw-rule">{{ r }}</div>
        <div v-if="!c.rules.length" class="empty">no rules</div>
      </div>
    </div>

    <!-- DHCP Leases -->
    <div v-if="tab==='dhcp'" class="tab-body">
      <table v-if="dhcp.length">
        <thead><tr><th>IP</th><th>MAC</th><th>Hostname</th><th>Expires</th></tr></thead>
        <tbody>
          <tr v-for="d in dhcp" :key="d.ip">
            <td class="mono">{{ d.ip }}</td><td class="mono">{{ d.mac }}</td><td>{{ d.hostname || '-' }}</td><td>{{ d.timestamp }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">No active DHCP leases</div>
    </div>

    <!-- Routes -->
    <div v-if="tab==='routes'" class="tab-body">
      <table v-if="routes.length">
        <thead><tr><th>Destination</th><th>Gateway</th><th>Interface</th><th>Proto</th></tr></thead>
        <tbody>
          <tr v-for="r in routes" :key="r.network">
            <td class="mono">{{ r.network }}</td><td class="mono">{{ r.nexthop||'*' }}</td><td>{{ r.dev }}</td><td>{{ r.proto }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const tab = ref('arp')
const tabs = [{id:'arp',label:'ARP'},{id:'dhcp',label:'DHCP'},{id:'fw',label:'Firewall'},{id:'routes',label:'Routes'}]
const arp = ref([]), fwChains = ref([]), dhcp = ref([]), routes = ref([])

async function fetchArp() { try{const r=await fetch('/api/ip/arp'); arp.value=(await r.json()).arp||[]; tabs[0].count=arp.value.length}catch{} }
async function fetchFW() { try{const r=await fetch('/api/ip/firewall'); fwChains.value=(await r.json()).chains||[]}catch{} }
async function fetchDHCP() { try{const r=await fetch('/api/ip/dhcp'); const d=await r.json(); dhcp.value=d.leases||[]; tabs[2].count=d.count}catch{} }
async function fetchRoutes() {
  try {
    const r = await fetch('/api/network/status'); const d = await r.json()
    routes.value = (d.routes||'').split('\n').filter(l=>l.trim()).map(l=>({network:l.split(' ')[0]||'', nexthop:l.split(' ')[2]||'', dev:l.split(' ')[4]||'', proto:l.split(' ')[0]||''}))
  } catch {}
}
onMounted(fetchArp)
</script>

<style scoped>
.ros-ip { display:flex; flex-direction:column; gap:0; }
.ros-tabs { display:flex; gap:0; border-bottom:2px solid var(--accent); margin-bottom:12px; }
.ros-tabs button { padding:6px 16px; background:none; border:none; color:var(--fg2); cursor:pointer; font-size:12px; font-weight:600; border-bottom:2px solid transparent; margin-bottom:-2px; display:flex; align-items:center; gap:4px; }
.ros-tabs button:hover { color:var(--fg); }
.ros-tabs button.sel { color:var(--accent); border-bottom-color:var(--accent); }
.ros-tabs .ct { background:var(--accent); color:#000; font-size:10px; padding:0 5px; border-radius:8px; min-width:16px; text-align:center; }
.tab-body { background:var(--bg2); border:1px solid var(--border); border-radius:0 0 4px 4px; padding:12px; }
.fw-chain { margin-bottom:12px; }
.fw-chain h3 { font-size:12px; color:var(--accent); margin-bottom:4px; font-family:var(--mono); }
.fw-rule { font-family:var(--mono); font-size:11px; color:var(--fg2); padding:2px 8px; border-left:2px solid var(--border); margin:2px 0; }
</style>
