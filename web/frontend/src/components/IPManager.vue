<template>
  <div class="ros-ip">
    <div class="ros-tabs">
      <button v-for="t in tabs" :key="t.id" :class="{sel: tab===t.id}" @click="switchTab(t.id)">
        {{ t.label }} <span v-if="t.count" class="ct">{{ t.count }}</span>
      </button>
    </div>

    <!-- ARP Table -->
    <div v-if="tab==='arp'" class="tab-body">
      <table>
        <thead><tr><th>IP Address</th><th>MAC Address</th><th>Vendor</th><th>Interface</th><th>State</th></tr></thead>
        <tbody>
          <tr v-for="a in arp" :key="a.ip">
            <td class="mono">{{ a.ip }}</td><td class="mono">{{ a.mac }}</td><td>{{ a.vendor || '––' }}</td><td>{{ a.dev }}</td>
            <td><span :class="'tag '+(a.state.toLowerCase())">{{ a.state }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Firewall (Filter/NAT/Mangle) -->
    <div v-if="['fw','nat','mangle'].includes(tab)" class="tab-body">
      <div class="fw-subtabs">
        <button :class="{sel: tab==='fw'}" @click="switchTab('fw')">Filter</button>
        <button :class="{sel: tab==='nat'}" @click="switchTab('nat')">NAT</button>
        <button :class="{sel: tab==='mangle'}" @click="switchTab('mangle')">Mangle</button>
        <button :class="{sel: natSub==='pf'}" @click="natSub='pf'; showPfTab=true" v-if="tab==='nat'">Port Forward</button>
      </div>
      <div v-for="c in fwFiltered" :key="c.name" class="fw-chain">
        <div class="fw-head">
          <h3>{{ c.family }} {{ c.table }} → {{ c.name }}</h3>
          <button class="btn-mini" @click="showAdd(c)">+ Add</button>
        </div>
        <!-- NAT presets -->
        <div v-if="tab==='nat' && c.name==='rnas-hotspot'" class="fw-presets">
          <button class="btn-preset" @click="quickAdd(c, 'udp dport 53 counter dnat to 192.168.0.203:53')">DNS→203</button>
          <button class="btn-preset" @click="quickAdd(c, 'tcp dport 80 counter dnat to 192.168.0.203:8099')">HTTP→8099</button>
          <button class="btn-preset" @click="quickAdd(c, 'tcp dport 443 counter dnat to 192.168.0.203:8099')">HTTPS→8099</button>
        </div>
        <div v-if="tab==='nat' && c.name==='postrouting'" class="fw-presets">
          <button class="btn-preset" @click="quickAdd(c, 'ip saddr 192.168.100.0/24 oifname ens33 counter masquerade')">Masquerade .100/24</button>
        </div>
        <div v-if="!c.rules.length" class="empty">no rules</div>
        <div v-for="(r,i) in c.rules" :key="i" class="fw-rule" :class="{disabled: r.disabled}">
          <div class="fw-bar-wrap"><div class="fw-bar" :style="{width: barWidth(r.packets, c)+'%'}"></div></div>
          <span class="fw-num pull-sml">#{{ i+1 }}</span>
          <span class="fw-text">{{ typeof r === 'string' ? r : r.text }}</span>
          <span class="fw-hit" v-if="r.packets !== undefined">({{ r.packets }}p/{{ fmtBytes(r.bytes||0) }})</span>
          <span class="fw-actions">
            <button v-if="i > 0" class="btn-move" @click="moveRule(c,i,'up')" title="Move up">▲</button>
            <button v-if="i < c.rules.length-1" class="btn-move" @click="moveRule(c,i,'down')" title="Move down">▼</button>
            <button v-if="r.handle" class="btn-toggle" :class="{on:!r.disabled}" @click="toggleRule(c,r)" title="Toggle rule">⏻</button>
            <button v-if="r.handle" class="btn-del" @click="delRule(c, r.handle)" title="Delete rule">✕</button>
          </span>
        </div>
        <div v-if="addTarget === c.name" class="fw-add">
          <input v-model="newRule" placeholder="e.g. tcp dport 443 accept" @keyup.enter="addRule(c)" />
          <button class="btn-mini" @click="addRule(c)">Add</button>
          <button class="btn-cancel" @click="addTarget=''">Cancel</button>
        </div>
      </div>
      <!-- Port Forward Wizard -->
      <div v-if="tab==='nat' && showPfTab" class="fw-pf">
        <h3>Port Forward</h3>
        <div class="pf-form">
          <select v-model="pfProto"><option value="tcp">TCP</option><option value="udp">UDP</option></select>
          <input v-model.number="pfPort" type="number" placeholder="External Port" min="1" max="65535" />
          <span>→</span>
          <input v-model="pfTarget" placeholder="Internal IP (e.g. 192.168.100.50)" />
          <input v-model.number="pfTargetPort" type="number" placeholder="Internal Port" min="1" max="65535" />
          <input v-model="pfDesc" placeholder="Description (optional)" class="pf-desc" />
          <button class="btn-mini" @click="addPortForward">Add</button>
        </div>
        <table v-if="pfRules.length">
          <thead><tr><th>Proto</th><th>Ext Port</th><th>→</th><th>Internal IP</th><th>Int Port</th><th>Desc</th><th></th></tr></thead>
          <tbody>
            <tr v-for="(r,i) in pfRules" :key="i">
              <td>{{ r.proto }}</td><td>{{ r.port }}</td><td>→</td><td class="mono">{{ r.target }}</td><td>{{ r.targetPort }}</td><td>{{ r.desc || '-' }}</td>
              <td><button class="btn-del always" @click="delPfRule(r)">✕</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- DHCP Leases -->
    <div v-if="tab==='dhcp'" class="tab-body">
      <table v-if="dhcp.length">
        <thead><tr><th>IP</th><th>MAC</th><th>Vendor</th><th>Hostname</th><th>Expires</th><th></th></tr></thead>
        <tbody>
          <tr v-for="d in dhcp" :key="d.ip">
            <td class="mono">{{ d.ip }}</td><td class="mono">{{ d.mac }}</td><td>{{ d.vendor || '––' }}</td><td>{{ d.hostname || '-' }}</td><td>{{ d.timestamp }}</td>
            <td><button class="btn-make-static" @click="makeStatic(d)" title="Make static binding">📌 Static</button></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">No active DHCP leases</div>
    </div>

    <!-- DHCP Static Leases -->
    <div v-if="tab==='static'" class="tab-body">
      <div class="fw-head"><h3>Static Leases</h3><button class="btn-mini" @click="showStaticAdd=!showStaticAdd">+ Add</button></div>
      <div v-if="showStaticAdd" class="fw-add">
        <input v-model="newStaticMac" placeholder="MAC (e.g. aa:bb:cc:dd:ee:ff)" />
        <input v-model="newStaticIp" placeholder="IP (e.g. 192.168.100.50)" />
        <input v-model="newStaticHost" placeholder="Hostname (optional)" class="short" />
        <button class="btn-mini" @click="addStatic">Add</button>
        <button class="btn-cancel" @click="showStaticAdd=false; newStaticMac=''; newStaticIp=''; newStaticHost=''">Cancel</button>
      </div>
      <table v-if="dhcpStatic.length">
        <thead><tr><th>MAC</th><th>IP</th><th>Hostname</th><th></th></tr></thead>
        <tbody>
          <tr v-for="s in dhcpStatic" :key="s.mac" :class="{disabled: !s.enabled}">
            <td class="mono">{{ s.mac }}</td><td class="mono">{{ s.ip }}</td><td>{{ s.hostname || '-' }}</td>
            <td><button class="btn-del always" @click="delStatic(s.mac)">✕</button></td>
          </tr>
        </tbody>
      </table>
      <div v-if="!dhcpStatic.length && !showStaticAdd" class="empty">No static leases</div>
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

    <!-- IP Addresses -->
    <div v-if="tab==='addr'" class="tab-body">
      <div class="fw-head"><h3>Interface IP Addresses</h3><button class="btn-mini" @click="showAddrAdd=!showAddrAdd">+ Add</button></div>
      <div v-if="showAddrAdd" class="fw-add">
        <input v-model="newAddrIface" placeholder="Interface name" />
        <input v-model="newAddrIp" placeholder="IP/CIDR" />
        <button class="btn-mini" @click="addAddr">Add</button>
        <button class="btn-cancel" @click="showAddrAdd=false; newAddrIface=''; newAddrIp=''">Cancel</button>
      </div>
      <table v-if="addrs.length">
        <thead><tr><th>Interface</th><th>IP Address</th><th>State</th><th></th></tr></thead>
        <tbody>
          <tr v-for="a in addrs" :key="a.name + a.ip" :class="{down: a.state !== 'UP'}">
            <td class="mono">{{ a.name }}</td><td class="mono">{{ a.ip }}</td>
            <td><span :class="'tag '+(a.state.toLowerCase())">{{ a.state }}</span></td>
            <td><button class="btn-del always" @click="delAddr(a.name, a.ip)" :disabled="a.name==='lo'">✕</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
const addToast = inject('addToast', () => {})

const TBL_MAP = { fw: 'filter', nat: 'nat', mangle: 'mangle' }
const tab = ref('arp')
const tabs = [ {id:'arp',label:'ARP'}, {id:'dhcp',label:'DHCP'}, {id:'static',label:'Static'}, {id:'fw',label:'Filter'}, {id:'nat',label:'NAT'}, {id:'mangle',label:'Mangle'}, {id:'routes',label:'Routes'}, {id:'addr',label:'Addresses'} ]
const arp = ref([]), fwChains = ref([]), dhcp = ref([]), routes = ref([]), dhcpStatic = ref([]), addrs = ref([])
const addTarget = ref(''), newRule = ref('')
const showStaticAdd = ref(false), newStaticMac = ref(''), newStaticIp = ref(''), newStaticHost = ref('')
const showAddrAdd = ref(false), newAddrIface = ref(''), newAddrIp = ref('')
const pfProto = ref('tcp'), pfPort = ref(80), pfTarget = ref(''), pfTargetPort = ref(80), pfDesc = ref('')
const showPfTab = ref(false), pfRules = ref([]), natSub = ref('')

const fwFiltered = computed(() => {
  const tbl = TBL_MAP[tab.value]
  if (!tbl) return fwChains.value
  return fwChains.value.filter(c => (c.table||'').toLowerCase() === tbl)
})

function switchTab(id) {
  tab.value = id
  if (id === 'arp') fetchArp()
  else if (['fw','nat','mangle'].includes(id)) fetchFW()
  else if (id === 'dhcp') fetchDHCP()
  else if (id === 'static') fetchStatic()
  else if (id === 'addr') fetchAddr()
  else if (id === 'routes') fetchRoutes()
}

async function fetchArp() { try{const r=await fetch('/api/ip/arp'); arp.value=(await r.json()).arp||[]; tabs[0].count=arp.value.length}catch{} }
async function fetchFW() { try{const r=await fetch('/api/ip/firewall-full'); fwChains.value=(await r.json()).chains||[]; parsePfRules()}catch(e){ try{const r2=await fetch('/api/ip/firewall'); fwChains.value=(await r2.json()).chains||[]}catch{}} }
async function fetchDHCP() { try{const r=await fetch('/api/ip/dhcp'); const d=await r.json(); dhcp.value=d.leases||[]; tabs[1].count=d.count}catch{} }
async function fetchStatic() { try{const r=await fetch('/api/ip/dhcp-static'); dhcpStatic.value=(await r.json()).static||[]}catch{} }
async function fetchAddr() { try{const r=await fetch('/api/ip/addresses'); addrs.value=(await r.json()).addresses||[]}catch{} }
async function fetchRoutes() {
  try {
    const r = await fetch('/api/network/status'); const d = await r.json()
    routes.value = (d.routes||'').split('\n').filter(l=>l.trim()).map(l=>({network:l.split(' ')[0]||'', nexthop:l.split(' ')[2]||'', dev:l.split(' ')[4]||'', proto:l.split(' ')[0]||''}))
  } catch {}
}

async function addStatic() {
  if (!newStaticMac.value.trim() || !newStaticIp.value.trim()) return
  try {
    await fetch('/api/ip/dhcp-static', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mac: newStaticMac.value.trim(), ip: newStaticIp.value.trim(), hostname: newStaticHost.value.trim() }) })
    showStaticAdd.value = false; newStaticMac.value = ''; newStaticIp.value = ''; newStaticHost.value = ''; fetchStatic(); addToast('Static lease added', 'ok')
  } catch {}
}
async function delStatic(mac) {
  if (!confirm(`Delete static lease for ${mac}?`)) return
  try {
    await fetch('/api/ip/dhcp-static', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mac }) })
    fetchStatic(); addToast('Static lease deleted', 'ok')
  } catch {}
}
async function addAddr() {
  const iface = newAddrIface.value.trim(), ip = newAddrIp.value.trim()
  if (!iface || !ip) return
  try {
    await fetch('/api/ip/addresses', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ iface, ip }) })
    showAddrAdd.value = false; newAddrIface.value = ''; newAddrIp.value = ''; fetchAddr()
  } catch {}
}
async function delAddr(iface, ip) {
  if (!confirm(`Remove ${ip} from ${iface}?`)) return
  try {
    await fetch('/api/ip/addresses', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ iface, ip }) })
    fetchAddr()
  } catch {}
}

function showAdd(chain) { addTarget.value = chain.name; newRule.value = '' }
async function quickAdd(chain, rule) {
  try {
    await fetch('/api/ip/firewall', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: chain.name, table: chain.table, family: chain.family, rule }) })
    fetchFW()
  } catch {}
}
function barWidth(pkts, chain) {
  const max = Math.max(...chain.rules.map(r => r.packets || 0), 1)
  return Math.min((pkts || 0) / max * 100, 100)
}
function fmtBytes(b) {
  if (b < 1024) return b + 'B'
  if (b < 1048576) return (b/1024).toFixed(1)+'K'
  return (b/1048576).toFixed(1)+'M'
}
async function moveRule(chain, idx, dir) {
  const r = chain.rules[idx]
  const swap = dir === 'up' ? chain.rules[idx-1] : chain.rules[idx+1]
  if (!r.handle || !swap.handle) return
  try {
    await fetch('/api/ip/firewall/reorder', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: chain.name, table: chain.table, family: chain.family, handle: r.handle, position: swap.handle }) })
    fetchFW()
  } catch {}
}
async function toggleRule(chain, rule) {
  if (!rule.handle) return
  try {
    await fetch(`/api/ip/firewall/${rule.handle}/toggle`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: chain.name, table: chain.table, family: chain.family, enabled: !!rule.disabled }) })
    fetchFW()
  } catch {}
}
function parsePfRules() {
  pfRules.value = []
  const natChain = fwChains.value.find(c => c.name === 'rnas-hotspot' && c.table === 'nat')
  if (!natChain) return
  for (const r of natChain.rules) {
    const t = typeof r === 'string' ? r : r.text
    const m = t.match(/(tcp|udp)\s+dport\s+(\d+)\s+counter\s+dnat\s+to\s+(\S+):(\d+)/)
    if (m) pfRules.value.push({ proto: m[1], port: m[2], target: m[3], targetPort: m[4], desc: '', handle: r.handle || 0 })
  }
}
async function addPortForward() {
  if (!pfTarget.value || !pfPort.value) return
  const rule = `${pfProto.value} dport ${pfPort.value} counter dnat to ${pfTarget.value}:${pfTargetPort.value}`
  const c = { name: 'rnas-hotspot', table: 'nat', family: 'ip' }
  try {
    await fetch('/api/ip/firewall', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: c.name, table: c.table, family: c.family, rule }) })
    fetchFW(); setTimeout(parsePfRules, 500)
    pfPort.value++; pfProto.value = 'tcp'; pfTarget.value = ''; pfTargetPort.value = 80; pfDesc.value = ''
  } catch {}
}
async function delPfRule(r) {
  if (!r.handle) return
  try {
    await fetch('/api/ip/firewall', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: 'rnas-hotspot', table: 'nat', family: 'ip', handle: r.handle }) })
    fetchFW(); setTimeout(parsePfRules, 500)
  } catch {}
}
function makeStatic(lease) {
  newStaticMac.value = lease.mac
  newStaticIp.value = lease.ip
  newStaticHost.value = lease.hostname || ''
  showStaticAdd.value = true
  tab.value = 'static'
}
async function addRule(chain) {
  if (!newRule.value.trim()) return
  try {
    await fetch('/api/ip/firewall', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: chain.name, table: chain.table, family: chain.family, rule: newRule.value.trim() }) })
    addTarget.value = ''; newRule.value = ''; fetchFW(); addToast('Rule added', 'ok')
  } catch {}
}
async function delRule(chain, handle) {
  if (!confirm(`Delete rule handle ${handle} from ${chain.name}?`)) return
  try {
    await fetch('/api/ip/firewall', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ chain: chain.name, table: chain.table, family: chain.family, handle }) })
    fetchFW(); addToast('Rule deleted', 'ok')
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
.fw-chain { margin-bottom:14px; position:relative; }
.fw-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:4px; }
.fw-head h3 { font-size:12px; color:var(--accent); font-family:var(--mono); }
.fw-rule { display:flex; align-items:center; gap:4px; font-family:var(--mono); font-size:10px; color:var(--fg2); padding:1px 6px; margin:1px 0; border-left:2px solid var(--border); position:relative; min-height:20px; }
.fw-rule:hover { background:rgba(10,189,227,0.04); }
.fw-rule.disabled { opacity:0.35; }
.fw-bar-wrap { position:absolute; left:0; top:0; height:100%; width:100%; pointer-events:none; }
.fw-bar { height:100%; background:rgba(10,189,227,0.07); border-radius:0 2px 2px 0; transition:width 0.5s; }
.fw-num { color:var(--fg3); font-size:9px; min-width:20px; z-index:1; }
.fw-text { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; z-index:1; }
.fw-hit { color:var(--fg3); font-size:9px; white-space:nowrap; z-index:1; }
.fw-actions { display:none; gap:2px; align-items:center; flex-shrink:0; z-index:1; }
.fw-rule:hover .fw-actions { display:flex; }
.btn-move { padding:0 4px; background:none; color:var(--fg3); border:none; cursor:pointer; font-size:9px; line-height:1; }
.btn-move:hover { color:var(--accent); }
.btn-toggle { padding:0 4px; background:none; color:var(--fg3); border:none; cursor:pointer; font-size:11px; line-height:1; }
.btn-toggle.on { color:var(--green); }
.btn-toggle:hover { color:var(--accent); }
.fw-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:4px; }
.fw-head h3 { font-size:12px; color:var(--accent); font-family:var(--mono); }
.fw-rule { display:flex; align-items:center; justify-content:space-between; font-family:var(--mono); font-size:11px; color:var(--fg2); padding:2px 8px; border-left:2px solid var(--border); margin:2px 0; }
.fw-rule:hover { background:rgba(10,189,227,0.04); }
.fw-text { flex:1; }
.btn-mini { padding:2px 10px; background:var(--bg3); color:var(--accent); border:1px solid var(--accent); border-radius:3px; cursor:pointer; font-size:10px; font-family:var(--font); }
.btn-mini:hover { background:var(--accent); color:#000; }
.btn-del { padding:1px 6px; background:none; color:var(--fg3); border:none; cursor:pointer; font-size:11px; opacity:0; transition:opacity .15s; }
.fw-rule:hover .btn-del { opacity:1; }
.btn-del:hover { color:var(--red); }
.btn-cancel { padding:2px 10px; background:none; color:var(--fg3); border:1px solid var(--border); border-radius:3px; cursor:pointer; font-size:10px; font-family:var(--font); margin-left:4px; }
.fw-add { display:flex; gap:6px; align-items:center; margin-top:6px; padding:6px 0; }
.fw-presets { display:flex; gap:4px; flex-wrap:wrap; margin-bottom:6px; }
.btn-preset { padding:2px 8px; background:var(--bg3); color:var(--accent); border:1px solid rgba(10,189,227,0.3); border-radius:3px; cursor:pointer; font-size:10px; font-family:var(--mono); }
.btn-preset:hover { background:var(--accent); color:#000; }
.fw-add input { flex:1; padding:4px 8px; background:var(--bg); color:var(--fg); border:1px solid var(--accent); border-radius:3px; font-family:var(--mono); font-size:11px; outline:none; }
.fw-add input.short { flex:0.5; }
.btn-del.always { opacity: 1; }
tr.disabled { opacity: 0.4; }
tr.down { opacity: 0.4; }
.tag { font-size:9px; padding:1px 6px; border-radius:3px; font-weight:600; }
.tag.reachable, .tag.up { background:rgba(16,172,132,0.15); color:var(--green); }
.tag.stale, .tag.unknown { background:rgba(131,149,167,0.15); color:var(--fg3); }
.tag.failed, .tag.down { background:rgba(238,82,83,0.15); color:var(--red); }
</style>
