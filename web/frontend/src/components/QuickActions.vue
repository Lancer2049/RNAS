<template>
  <div class="quick-actions">
    <h3>Quick Actions</h3>
    <div class="actions-grid">
      <div class="action-card" @click="$emit('nav','subscriber-sim')">
        <span class="icon">👥</span><span class="label">Simulate Subscribers</span>
      </div>
      <div class="action-card" @click="$emit('nav','scenario-runner')">
        <span class="icon">▶</span><span class="label">Run Scenario</span>
      </div>
      <div class="action-card" @click="$emit('nav','radius-editor')">
        <span class="icon">🔧</span><span class="label">RADIUS Test</span>
      </div>
      <div class="action-card" @click="$emit('nav','sniffer')">
        <span class="icon">📡</span><span class="label">Capture Packets</span>
      </div>
      <div class="action-card" @click="$emit('refresh')">
        <span class="icon">🔄</span><span class="label">Refresh All</span>
      </div>
      <div class="action-card" @click="window.open('http://192.168.0.202:8000','_blank')">
        <span class="icon">🔗</span><span class="label">Open AirOS</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['nav','refresh'])
</script>

<style scoped>
.quick-actions { margin-bottom: 16px; }
.quick-actions h3 { font-size: 12px; color: var(--fg2); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
.actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
.action-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 3px; padding: 14px 16px; display: flex; flex-direction: column; align-items: center; gap: 6px; cursor: pointer; transition: all 0.15s; }
.action-card:hover { border-color: var(--accent); background: rgba(10,189,227,0.06); transform: translateY(-1px); }
.action-card .icon { font-size: 22px; }
.action-card .label { font-size: 11px; color: var(--fg2); font-weight: 500; text-align: center; }
</style>
