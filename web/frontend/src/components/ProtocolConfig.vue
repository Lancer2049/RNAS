<template>
  <div class="proto-config">
    <h2 class="page-title">Protocol Configuration</h2>
    <p class="page-hint">Configure access protocols — changes require Apply to take effect</p>

    <div class="proto-tabs">
      <button v-for="p in protocols" :key="p.id" :class="{active:active===p.id}" @click="active=p.id;loadProto(p.id)">
        {{ p.icon }} {{ p.name }}
        <span class="status-dot" :class="loaded ? (p.enabled?'on':'off') : 'loading'"></span>
      </button>
    </div>

    <div class="proto-form" v-if="current">
      <div class="form-header">
        <label class="toggle">
          <input type="checkbox" v-model="current.enabled" @change="save" />
          <span>{{ current.enabled ? 'Enabled' : 'Disabled' }}</span>
        </label>
      </div>

      <div class="field-group">
        <div class="field-group-title">Basic Settings</div>
        <div class="field-row" v-for="f in current.fields.filter(f=>['enabled','interface','port','ac_name','service_name','mtu','mru','accept','ssl_pemfile','mode','start','ip_pool','opt_src'].includes(f.key))" :key="f.key">
          <label>{{ f.label }}</label>
          <select v-if="f.key==='interface'" v-model="current.values[f.key]" class="field-input">
            <option v-for="iface in interfaces" :key="iface" :value="iface">{{ iface }}</option>
          </select>
          <select v-else-if="f.type==='yesno'" v-model="current.values[f.key]" class="field-input">
            <option value="yes">yes</option><option value="no">no</option>
          </select>
          <input v-else :type="f.type||'text'" v-model="current.values[f.key]" :placeholder="f.default" class="field-input" />
          <span class="field-hint">{{ f.hint }}</span>
        </div>
      </div>

      <div class="field-group">
        <div class="field-group-title" @click="showAdvanced=!showAdvanced" style="cursor:pointer;user-select:none">
          {{ showAdvanced ? '▼' : '▶' }} Advanced Settings
        </div>
        <template v-if="showAdvanced">
          <div class="field-row" v-for="f in current.fields.filter(f=>!['enabled','interface','port','ac_name','service_name','mtu','mru','accept','ssl_pemfile','mode','start','ip_pool','opt_src'].includes(f.key))" :key="f.key">
            <label>{{ f.label }}</label>
            <input :type="f.type||'text'" v-model="current.values[f.key]" :placeholder="f.default" class="field-input" />
            <span class="field-hint">{{ f.hint }}</span>
          </div>
        </template>
      </div>

      <div class="form-actions">
        <button class="btn-primary" @click="save" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        <button class="btn-primary" @click="apply" :disabled="applying">{{ applying ? 'Applying...' : 'Apply & Restart' }}</button>
        <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const active = ref('pppoe')
const current = ref(null)
const saving = ref(false), applying = ref(false)
const msg = ref(''), msgType = ref('ok')
const interfaces = ref(['ens33','lo','eth0'])
const showAdvanced = ref(false)
const loaded = ref(false)

const protocols = reactive([
  {id:'pppoe',name:'PPPoE',icon:'📡',enabled:false,section:'access.d.pppoe', module:'pppoe',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'Physical interface for PPPoE'},
      {key:'ac_name',label:'AC Name',default:'RNAS',hint:'Access Concentrator name'},
      {key:'service_name',label:'Service Name',default:'',hint:'Optional service name filter'},
      {key:'mtu',label:'MTU',type:'number',default:'1492',hint:'576-1500'},
      {key:'mru',label:'MRU',type:'number',default:'1492',hint:'576-1500'},
      {key:'min_mtu',label:'Min MTU',type:'number',default:'1280',hint:'Minimum acceptable MTU'},
      {key:'lcp_echo_interval',label:'LCP Echo Interval',type:'number',default:'30',hint:'Seconds between keepalives'},
      {key:'lcp_echo_failure',label:'LCP Echo Failure',type:'number',default:'3',hint:'Failures before disconnect'},
      {key:'session_timeout',label:'Session Timeout',type:'number',default:'0',hint:'0=unlimited seconds'},
      {key:'idle_timeout',label:'Idle Timeout',type:'number',default:'0',hint:'0=unlimited seconds'},
      {key:'max_sessions',label:'Max Sessions',type:'number',default:'1000',hint:'PPPoE session limit'},
      {key:'padi_timeout',label:'PADI Timeout',type:'number',default:'5',hint:'PPPoE discovery timeout'},
      {key:'padr_timeout',label:'PADR Timeout',type:'number',default:'5',hint:'PPPoE request timeout'},
    ]},
  {id:'l2tp',name:'L2TP',icon:'🛡',enabled:false,section:'access.d.l2tp', module:'l2tp',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'Listen interface'},
      {key:'port',label:'Port',type:'number',default:'1701',hint:'1-65535'},
      {key:'mtu',label:'MTU',type:'number',default:'1460',hint:'576-1500'},
      {key:'mru',label:'MRU',type:'number',default:'1460',hint:'576-1500'},
      {key:'hello_interval',label:'Hello Interval',type:'number',default:'60',hint:'L2TP hello keepalive'},
      {key:'recv_window',label:'Receive Window',type:'number',default:'16',hint:'L2TP receive window size'},
      {key:'retransmit_timeout',label:'Retransmit Timeout',type:'number',default:'1',hint:'Seconds'},
      {key:'retransmit_retries',label:'Retransmit Retries',type:'number',default:'5',hint:'Max retransmit attempts'},
      {key:'lcp_echo_interval',label:'LCP Echo Interval',type:'number',default:'30',hint:'Seconds'},
      {key:'lcp_echo_failure',label:'LCP Echo Failure',type:'number',default:'3',hint:'Failures'},
      {key:'session_timeout',label:'Session Timeout',type:'number',default:'0',hint:'Seconds'},
    ]},
  {id:'pptp',name:'PPTP',icon:'🔒',enabled:false,section:'access.d.pptp', module:'pptp',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'Listen interface'},
      {key:'mtu',label:'MTU',type:'number',default:'1436',hint:'576-1500'},
      {key:'mru',label:'MRU',type:'number',default:'1436',hint:'576-1500'},
      {key:'lcp_echo_interval',label:'LCP Echo Interval',type:'number',default:'30',hint:'Seconds'},
      {key:'lcp_echo_failure',label:'LCP Echo Failure',type:'number',default:'3',hint:'Failures'},
      {key:'session_timeout',label:'Session Timeout',type:'number',default:'0',hint:'Seconds'},
      {key:'idle_timeout',label:'Idle Timeout',type:'number',default:'0',hint:'Seconds'},
    ]},
  {id:'sstp',name:'SSTP',icon:'🔐',enabled:false,section:'access.d.sstp', module:'sstp',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'Listen interface'},
      {key:'port',label:'Port',type:'number',default:'443',hint:'1-65535'},
      {key:'accept',label:'Accept Mode',default:'ssl',hint:'ssl/proxy'},
      {key:'ssl_pemfile',label:'SSL Certificate',default:'/etc/rnas/ssl/sstp.pem',hint:'Path to PEM file'},
      {key:'ssl_key',label:'SSL Key',default:'/etc/rnas/ssl/sstp.key',hint:'Path to key file'},
      {key:'mtu',label:'MTU',type:'number',default:'1400',hint:'576-1500'},
      {key:'mru',label:'MRU',type:'number',default:'1400',hint:'576-1500'},
      {key:'lcp_echo_interval',label:'LCP Echo Interval',type:'number',default:'30',hint:'Seconds'},
      {key:'lcp_echo_failure',label:'LCP Echo Failure',type:'number',default:'3',hint:'Failures'},
      {key:'session_timeout',label:'Session Timeout',type:'number',default:'0',hint:'Seconds'},
      {key:'idle_timeout',label:'Idle Timeout',type:'number',default:'0',hint:'Seconds'},
    ]},
  {id:'ipoe',name:'IPoE',icon:'🌐',enabled:false,section:'access.d.ipoe', module:'ipoe',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'DHCP snooping interface'},
      {key:'mode',label:'Mode',default:'L2',hint:'L2 (DHCP snoop) or L3 (IP subnet)'},
      {key:'start',label:'Start Type',default:'dhcpv4',hint:'dhcpv4 / arp / dhcpv6'},
      {key:'ip_pool',label:'IP Pool',default:'default',hint:'Pool name from ip-pool.conf'},
      {key:'opt_src',label:'Gateway IP',default:'192.168.100.1',hint:'Default gateway for clients'},
      {key:'lease_time',label:'Lease Time',type:'number',default:'3600',hint:'DHCP lease duration seconds'},
      {key:'session_timeout',label:'Session Timeout',type:'number',default:'0',hint:'Seconds'},
      {key:'idle_timeout',label:'Idle Timeout',type:'number',default:'0',hint:'Seconds'},
    ]},
  {id:'mac_auth',name:'MAC Auth',icon:'🖧',enabled:false,section:'access.d.mac_auth', module:'mac_auth',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'DHCP snooping interface (IPoE L2)'},
      {key:'username_format',label:'Username Format',default:'mac',hint:'mac / ifname'},
      {key:'nas_identifier',label:'NAS Identifier',default:'rnas-mac-auth',hint:'NAS-Identifier attr'},
      {key:'ip_pool',label:'IP Pool',default:'default',hint:'Pool name from ip-pool.conf'},
      {key:'vlan',label:'VLAN',type:'number',hint:'Optional 802.1Q tag'},
    ]},
  {id:'dot1x',name:'802.1X',icon:'🔑',enabled:false,section:'wireless.d.dot1x', module:'dot1x',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'interface',label:'Interface',hint:'Dedicated veth/bridge (never mgmt iface)'},
      {key:'auth_server',label:'Auth Server',default:'192.168.0.202',hint:'FreeRADIUS EAP server'},
      {key:'auth_port',label:'Auth Port',type:'number',default:'1812',hint:'RADIUS auth port'},
      {key:'auth_secret',label:'Secret',default:'testing123',hint:'RADIUS shared secret'},
      {key:'nas_identifier',label:'NAS Identifier',default:'rnas-dot1x',hint:'NAS-Identifier attr'},
      {key:'eap_methods',label:'EAP Methods',default:'md5,peap,tls',hint:'Accepted EAP methods'},
    ]},
  {id:'ipv6',name:'IPv6',icon:'🌍',enabled:false,section:'network.d.ipv6', module:'ipv6',
    fields:[
      {key:'enabled',label:'Enabled',type:'yesno',hint:''},
      {key:'prefix',label:'Prefix Pool',default:'fc00::/64',hint:'Assignable IPv6 prefix'},
      {key:'delegate',label:'Delegate',default:'fc00::/56',hint:'Delegated prefix from upstream'},
      {key:'dns',label:'DNS',default:'2001:4860:4860::8888',hint:'DHCPv6 DNS servers (comma sep)'},
      {key:'domain',label:'Domain',default:'rnas.local',hint:'DHCPv6 search domain'},
      {key:'ra_interval',label:'RA Interval',type:'number',default:'30',hint:'SLAAC RA interval seconds'},
    ]},
])

let configCache = null

async function loadProto(id) {
  const p = protocols.find(p=>p.id===id); if (!p) return
  current.value = { ...p, values: {...Object.fromEntries(p.fields.filter(f=>f.default).map(f=>[f.key, f.default]))} }
  try {
    if (!configCache) {
      const r = await fetch('/api/config')
      configCache = (await r.json()).config || {}
    }
    const data = configCache[p.section] || {}
    const core = configCache['access.d.core'] || {}
    p.enabled = (p.module === 'dot1x' || p.module === 'ipv6' || p.module === 'mac_auth')
      ? data.enabled === 'yes'
      : core[p.module] === 'yes'
    current.value = { ...p, values: {...data} }
    current.value.enabled = p.enabled
    loaded.value = true
  } catch { loaded.value = true }
}

async function save() {
  if (!current.value) return; saving.value = true
  const p = protocols.find(p=>p.id===active.value); if (!p) return
  try {
    const values = {...current.value.values}
    if (p.module === 'dot1x' || p.module === 'ipv6' || p.module === 'mac_auth') values.enabled = current.value.enabled ? 'yes' : 'no'
    await fetch(`/api/config/${p.module}`, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)})
    // dot1x/ipv6/mac_auth keep their own enabled flag; others flip access.d.core module
    if (p.module === 'dot1x' || p.module === 'ipv6' || p.module === 'mac_auth') {
      if (p.module === 'ipv6') {
        // Dual-stack needs ipv6=allow in the PPP section (ppp.conf) + modules in core.conf
        const ppp = await (await fetch('/api/config/ppp')).json()
        const pppValues = {...(ppp.config?.['access.d.ppp'] || {})}
        pppValues.ipv6 = current.value.enabled ? 'allow' : 'deny'
        await fetch('/api/config/ppp', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(pppValues)})
        const mods = {}
        for (const m of ['ipv6_dhcp','ipv6_nd','ipv6pool']) mods[m] = current.value.enabled ? 'yes' : 'no'
        await fetch('/api/config/modules', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(mods)})
      }
    } else {
      await fetch('/api/config/core', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({[p.module]:current.value.enabled?'yes':'no'})})
    }
    p.enabled = current.value.enabled
    msg.value='Saved'; msgType.value='ok'
  } catch { msg.value='Save failed'; msgType.value='err' }
  saving.value = false
}

async function apply() {
  applying.value = true
  msg.value = 'Restarting services...'; msgType.value = 'info'
  try {
    await fetch('/api/config/apply', {method:'POST'})
    msg.value='Applied & restarted'; msgType.value='ok'
  } catch { msg.value='Apply failed'; msgType.value='err' }
  applying.value = false
}

async function loadInterfaces() {
  try { const r = await fetch('/api/network/status'); const d = await r.json(); interfaces.value = (d.interfaces||[]).map(i=>i.name).filter(n=>n!=='lo') } catch {}
}

onMounted(() => { loadProto('pppoe'); loadInterfaces() })
</script>

<style scoped>
.proto-config{display:flex;flex-direction:column;gap:14px}
.page-title{font-size:15px;color:var(--fg);font-weight:600}
.page-hint{font-size:11px;color:var(--fg3)}
.proto-tabs{display:flex;gap:4px;flex-wrap:wrap}
.proto-tabs button{padding:6px 14px;border:1px solid var(--border);background:var(--bg);border-radius:3px 3px 0 0;cursor:pointer;font-size:12px;display:flex;align-items:center;gap:6px;transition:all .15s;color:var(--fg2);font-family:var(--font)}
.proto-tabs button.active{background:var(--accent);color:#000;border-color:var(--accent);font-weight:600}
.proto-tabs button:hover:not(.active){background:var(--bg3)}
.status-dot{width:8px;height:8px;border-radius:50%}.status-dot.on{background:var(--green)}.status-dot.off{background:var(--border)}.status-dot.loading{background:var(--fg3);opacity:0.4;animation:pulse 1s infinite}@keyframes pulse{0%,100%{opacity:0.4}50%{opacity:1}}
.proto-tabs button.active .status-dot.off{background:rgba(0,0,0,.3)}
.proto-form{background:var(--bg2);padding:14px;border-radius:0 3px 3px 3px;border:1px solid var(--border)}
.form-header{margin-bottom:14px}
.toggle{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;font-weight:600;color:var(--fg)}
.toggle input{width:18px;height:18px;accent-color:var(--accent)}
.field-row{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.field-row label{width:140px;font-size:11px;color:var(--fg3);flex-shrink:0}
.field-input{padding:4px 8px;border:1px solid var(--border);border-radius:3px;font-size:12px;flex:1;max-width:300px;background:var(--bg);color:var(--fg);font-family:var(--mono);outline:none}
.field-input:focus{border-color:var(--accent)}
.field-hint{font-size:9px;color:var(--fg3);width:100px}
.field-group{margin-bottom:14px;padding:12px;background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.03);border-radius:var(--radius)}
.field-group-title{font-size:11px;color:var(--fg2);font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px}
.form-actions{display:flex;gap:10px;align-items:center;margin-top:14px;padding-top:10px;border-top:1px solid var(--border)}
.btn-primary{padding:5px 16px;background:var(--bg3);color:var(--accent);border:1px solid var(--accent);border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font)}
.btn-primary:hover{background:var(--accent);color:#000}
.btn-primary:disabled{opacity:0.4}
.msg{font-size:12px;font-weight:500}.ok{color:var(--green)}.err{color:var(--red)}.info{color:var(--accent)}
</style>
