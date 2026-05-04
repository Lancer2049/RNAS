<template>
  <div class="status-grid">
    <div class="card">
      <div class="card-label">Uptime</div>
      <div class="card-value">{{ service.uptime || '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">Sessions</div>
      <div class="card-value">{{ service.sessions_active ?? '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">RADIUS</div>
      <div class="card-value" :class="service.radius_state==='active'?'text-green':'text-red'">{{ service.radius_state || '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">Auth Sent</div>
      <div class="card-value">{{ service.auth_sent || 0 }}</div>
    </div>
    <div class="card">
      <div class="card-label">Acct Sent</div>
      <div class="card-value">{{ service.acct_sent || 0 }}</div>
    </div>
    <div class="card">
      <div class="card-label">Failures</div>
      <div class="card-value" :class="service.radius_fail_count>0?'text-red':''">{{ service.radius_fail_count || 0 }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({ service: Object })
</script>

<style scoped>
.status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
.card { background: #fff; padding: 16px 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 3px solid #3b82f6; }
.card-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.card-value { font-size: 22px; font-weight: 700; }
.text-green { color: #22c55e; }
.text-red { color: #ef4444; }
</style>
