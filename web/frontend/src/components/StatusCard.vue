<template>
  <div class="ros-status">
    <div class="stat-grid">
      <div class="stat"><span class="sl">Uptime</span><span class="sv">{{ service.uptime || '--' }}</span></div>
      <div class="stat"><span class="sl">CPU</span><span class="sv">{{ service.cpu || '--' }}</span></div>
      <div class="stat"><span class="sl">RAM</span><span class="sv">{{ service.mem || '--' }}</span></div>
      <div class="stat">
        <span class="sl">RADIUS</span>
        <span class="sv" :style="{color: service.radius_state==='active'?'var(--green)':'var(--red)'}">
          {{ service.radius_state === 'active' ? '● UP' : '○ DOWN' }}
        </span>
      </div>
      <div class="stat"><span class="sl">Sessions</span><span class="sv">{{ service.sessions_active || 0 }} active</span></div>
      <div class="stat"><span class="sl">Auth Sent</span><span class="sv">{{ service.auth_sent || 0 }}</span></div>
      <div class="stat"><span class="sl">Acct Sent</span><span class="sv">{{ service.acct_sent || 0 }}</span></div>
      <div class="stat"><span class="sl">Radius Fails</span><span class="sv" :style="{color: (service.radius_fail_count||0) > 0 ? 'var(--red)' : 'inherit'}">{{ service.radius_fail_count || 0 }}</span></div>
    </div>
  </div>
</template>

<script setup>
defineProps({ service: { type: Object, default: () => ({}) } })
</script>

<style scoped>
.ros-status { background: var(--bg2); border: 1px solid var(--border); padding: 10px 14px; margin-bottom: 12px; border-radius: 3px; }
.stat-grid { display: flex; gap: 24px; flex-wrap: wrap; }
.stat { display: flex; flex-direction: column; gap: 2px; min-width: 80px; }
.sl { font-size: 9px; text-transform: uppercase; color: var(--fg3); letter-spacing: 1px; }
.sv { font-size: 14px; font-weight: 700; font-family: var(--mono); color: var(--fg); }
</style>
