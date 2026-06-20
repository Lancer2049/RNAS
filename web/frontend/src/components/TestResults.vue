<template>
  <div class="test-page">
    <h2 class="page-title">Test Results</h2>
    <p class="page-hint">Recent test runs — click to view details</p>

    <div class="test-card" v-if="regression">
      <div class="test-header">
        <h3>🧪 Regression Test</h3>
        <span class="badge" :class="regressionPassed ? 'pass' : 'fail'">{{ regressionPassed ? 'PASS' : 'FAIL' }}</span>
      </div>
      <pre class="test-output">{{ regression }}</pre>
    </div>
    <div class="test-card" v-else>
      <h3>🧪 Regression Test</h3>
      <p class="empty">Not yet run</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
const regression = ref('')
const regressionPassed = computed(() => regression.value.includes('0 failed'))

async function load() {
  try {
    const r = await fetch('/api/test/results')
    const d = await r.json()
    regression.value = d.regression || ''
  } catch {}
}
onMounted(load)
</script>

<style scoped>
.test-page{display:flex;flex-direction:column;gap:14px}
.page-title{font-size:15px;color:var(--fg);font-weight:600} .page-hint{font-size:11px;color:var(--fg3)}
.test-card{background:var(--bg2);padding:14px;border:1px solid var(--border);border-radius:3px}
.test-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.test-header h3{font-size:13px;color:var(--fg)}
.badge{padding:3px 12px;border-radius:6px;font-size:10px;font-weight:700}
.badge.pass{background:rgba(16,172,132,0.12);color:var(--green)}.badge.fail{background:rgba(238,82,83,0.12);color:var(--red)}
.test-output{background:#0a0f14;color:var(--green);padding:12px;border-radius:3px;font-family:var(--mono);font-size:11px;max-height:400px;overflow-y:auto;white-space:pre-wrap;border:1px solid var(--border)}
.empty{color:var(--fg3);font-size:12px;padding:20px}
</style>
