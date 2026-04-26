<template>
  <div class="status-grid">
    <div class="card">
      <div class="card-label">Service Uptime</div>
      <div class="card-value">{{ service.uptime || '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">CPU</div>
      <div class="card-value">{{ service.cpu || '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">Memory</div>
      <div class="card-value">{{ service.mem || '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">Sessions</div>
      <div class="card-value">{{ service.sessions_active ?? '--' }}</div>
    </div>
    <div class="card">
      <div class="card-label">RADIUS State</div>
      <div class="card-value" :class="radiusClass">{{ service.radius_state || '--' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ service: Object })

const radiusClass = computed(() => ({
  'text-green': props.service?.radius_state === 'active',
  'text-red': props.service?.radius_state !== 'active'
}))
</script>

<style scoped>
.status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card-label { font-size: 12px; color: #888; text-transform: uppercase; margin-bottom: 8px; }
.card-value { font-size: 24px; font-weight: 600; }
.text-green { color: #22c55e; }
.text-red { color: #ef4444; }
</style>
