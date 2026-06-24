<template>
  <div class="config-section">
    <div class="section-header">
      <h2>Configuration</h2>
      <p class="hint">Low-level configuration editor — most settings are available in dedicated pages</p>
    </div>

    <div class="cfg-layout">
      <div class="cfg-sidebar">
        <input v-model="filter" placeholder="Search..." class="cfg-search" />
        <div v-for="(grp, gname) in grouped" :key="gname" class="cfg-group">
          <div class="cfg-group-label">{{ gname }}</div>
          <div v-for="m in grp" :key="m" class="cfg-item" :class="{sel: selectedModule===m}" @click="selectedModule=m;loadModule()">{{ friendlyName(m) }}</div>
        </div>
      </div>

      <div class="cfg-editor">
        <div v-if="selectedModule && currentValues" class="editor-card">
          <h3>{{ friendlyName(selectedModule) }}</h3>
          <div class="field-row" v-for="(val, key) in currentValues" :key="key">
            <label>{{ key }}</label>
            <select v-if="isYesNo(val, key)" v-model="currentValues[key]" class="field-input">
              <option value="yes">yes</option><option value="no">no</option>
            </select>
            <input v-else-if="isPort(key)" v-model.number="currentValues[key]" type="number" min="1" max="65535" class="field-input" />
            <input v-else-if="isNumber(key)" v-model.number="currentValues[key]" type="number" class="field-input" />
            <input v-else v-model="currentValues[key]" :placeholder="val || '...'" class="field-input" />
            <span class="field-hint" v-if="isYesNo(val,key)||isPort(key)||isNumber(key)">{{ typeHint(val,key) }}</span>
          </div>
          <div class="actions">
            <button class="btn-save" @click="saveConfig" :disabled="!selectedModule || saving">{{ saving ? '...' : 'Save' }}</button>
            <button class="btn-apply" @click="applyConfig" :disabled="applying">{{ applying ? '...' : 'Apply' }}</button>
            <span v-if="message" class="msg" :class="messageType">{{ message }}</span>
          </div>
        </div>
        <div v-else class="empty-state">Select a section from the left panel</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const modules = ref([])
const selectedModule = ref('')
const currentValues = ref(null)
const saving = ref(false), applying = ref(false)
const message = ref(''), messageType = ref('success')
const filter = ref('')

const CATEGORIES = {
  'Access Protocols': ['pppoe','l2tp','pptp','sstp','ipoe'],
  'Core': ['global','core'],
  'RADIUS': ['radius'],
  'IP Pool': ['ip_pool','ipoe_pool'],
  'PPP': ['ppp'],
  'Network': ['interfaces','dhcp','dns','firewall','qos','ipv6','vlan','relay','zone'],
  'VPN': ['ipsec','wireguard','openvpn'],
  'Tunnels': ['gre','ipip','eoip','vxlan'],
  'Auth/AAA': ['dot1x','mac_auth','auth_pap','auth_chap_md5','auth_mschap_v1','auth_mschap_v2'],
  'Monitoring': ['snmp','netflow','log'],
  'HA': ['ha'],
  'Hotspot': ['hotspot'],
  'Other': [],
}

function friendlyName(m) {
  const map = {
    'core':'Core Settings','pppoe':'PPPoE Config','l2tp':'L2TP Config','pptp':'PPTP Config',
    'sstp':'SSTP Config','ipoe':'IPoE Config','radius':'RADIUS Server',
    'ip_pool':'IP Address Pool','interfaces':'Network Interfaces','dhcp':'DHCP Server',
    'dns':'DNS Forwarding','firewall':'Firewall Rules','qos':'QoS / Traffic Shaping',
    'ipv6':'IPv6 Configuration','vlan':'VLAN Assignment','relay':'DHCP Relay',
    'zone':'Firewall Zones','ipsec':'IPsec VPN','wireguard':'WireGuard VPN',
    'openvpn':'OpenVPN','gre':'GRE Tunnel','ipip':'IPIP Tunnel','eoip':'EoIP Tunnel',
    'vxlan':'VXLAN Tunnel','dot1x':'802.1X Authentication','mac_auth':'MAC Auth Bypass',
    'snmp':'SNMP Monitoring','netflow':'NetFlow Export','log':'Logging',
    'ha':'High Availability (VRRP)','hotspot':'Hotspot Portal',
    'auth_pap':'PAP Authentication','auth_chap_md5':'CHAP MD5 Auth',
    'auth_mschap_v1':'MS-CHAP v1 Auth','auth_mschap_v2':'MS-CHAP v2 Auth',
    'global':'Global Settings','ppp':'PPP Options',
  }
  return map[m] || m.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())
}

function categorize(name) {
  const key = name.split('.')[0]  // e.g. "access.d.pppoe" → "access"
  if (name.startsWith('access.d.')) return friendlyName(name.split('.')[2]) || 'Access Protocols'
  if (name.startsWith('network.d.')) return 'Network'
  if (name.startsWith('vpn.d.')) return 'VPN'
  if (name.startsWith('tunnel.')) return 'Tunnels'
  for (const [cat, items] of Object.entries(CATEGORIES)) {
    if (items.some(i => name.includes(i))) return cat
  }
  return 'Other'
}

const grouped = computed(() => {
  const g = {}
  const q = filter.value.toLowerCase()
  for (const m of modules.value) {
    if (q && !friendlyName(m).toLowerCase().includes(q) && !m.toLowerCase().includes(q)) continue
    const cat = categorize(m)
    if (!g[cat]) g[cat] = []
    g[cat].push(m)
  }
  // Sort within each group
  for (const cat of Object.keys(g)) g[cat].sort()
  return g
})

async function loadModules() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    modules.value = Object.keys(data.config || {})
  } catch {}
}

async function loadModule() {
  if (!selectedModule.value) return
  try {
    const res = await fetch(`/api/config/${selectedModule.value.replace('.', '/')}`)
    const data = await res.json()
    const matches = data.config || {}
    currentValues.value = { ...matches[selectedModule.value] }
  } catch {}
}

async function saveConfig() {
  saving.value = true
  try {
    const res = await fetch(`/api/config/${selectedModule.value.replace('.', '/')}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentValues.value)
    })
    message.value = res.ok ? 'Saved' : 'Save failed'
    messageType.value = res.ok ? 'success' : 'error'
  } catch { message.value = 'Network error'; messageType.value = 'error' }
  saving.value = false
}

async function applyConfig() {
  applying.value = true
  try { await fetch('/api/config/apply', { method: 'POST' }); message.value = 'Applied'; messageType.value = 'success' }
  catch { message.value = 'Apply failed'; messageType.value = 'error' }
  applying.value = false
}

function isYesNo(v,k){ return v==='yes'||v==='no'||k.includes('enabled')||k==='daemon'||k==='auth'||k.includes('check_') }
function isPort(k){ return k.includes('port') }
function isNumber(k){ return k.includes('timeout')||k.includes('interval')||k.includes('limit')||k.includes('count')||k.includes('thread')||k.includes('max')||k.includes('weight') }
function typeHint(v,k){ if(isYesNo(v,k))return 'yes/no'; if(isPort(k))return '1-65535'; if(isNumber(k))return 'number'; return '' }

onMounted(loadModules)
</script>

<style scoped>
.config-section{display:flex;flex-direction:column;gap:12px}
.section-header h2{font-size:15px;color:var(--fg);font-weight:600}
.hint{font-size:11px;color:var(--fg3)}
.cfg-layout{display:grid;grid-template-columns:220px 1fr;gap:14px;align-items:start}
.cfg-sidebar{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:8px;max-height:65vh;overflow-y:auto}
.cfg-search{width:100%;padding:6px 8px;border:1px solid var(--border);border-radius:3px;background:var(--bg);color:var(--fg);font-size:11px;font-family:var(--font);outline:none;margin-bottom:6px}
.cfg-search:focus{border-color:var(--accent)}
.cfg-group{margin-bottom:6px}
.cfg-group-label{font-size:9px;color:var(--fg3);text-transform:uppercase;letter-spacing:1px;padding:4px 6px;font-weight:700}
.cfg-item{padding:4px 8px;font-size:11px;color:var(--fg2);cursor:pointer;border-radius:3px}
.cfg-item:hover{background:var(--bg3);color:var(--fg)}
.cfg-item.sel{background:rgba(10,189,227,0.08);color:var(--accent);font-weight:600}
.cfg-editor{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:14px;min-height:200px}
.editor-card h3{font-size:12px;color:var(--fg2);margin-bottom:10px;font-family:var(--mono);text-transform:uppercase;letter-spacing:1px}
.field-row{display:grid;grid-template-columns:200px 1fr;gap:8px;margin-bottom:6px;align-items:center}
.field-row label{font-size:11px;color:var(--fg3);font-family:var(--mono)}
.field-input{padding:4px 8px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:var(--bg);color:var(--fg);font-family:var(--mono);outline:none}
.field-input:focus{border-color:var(--accent)}
.field-hint{font-size:9px;color:var(--fg3)}
.actions{display:flex;gap:8px;align-items:center;margin-top:12px}
.btn-save,.btn-apply{padding:5px 14px;border:none;border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.btn-save{background:var(--green);color:#000}
.btn-apply{background:var(--accent);color:#000}
.btn-save:disabled,.btn-apply:disabled{opacity:0.4}
.msg{font-size:11px;font-weight:600}
.msg.success{color:var(--green)}.msg.error{color:var(--red)}
.empty-state{text-align:center;padding:40px;color:var(--fg3);font-size:12px}
</style>
