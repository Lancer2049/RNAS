<template>
  <div class="dictionary-section">
    <div class="section-header">
      <h2>RADIUS Dictionary</h2>
      <div class="search-bar">
        <input v-model="query" placeholder="Search attributes..." @input="search" />
        <span class="count">{{ filtered.length }} / {{ totalCount }} attrs</span>
      </div>
    </div>

    <div class="dict-layout">
      <div class="vendor-list">
        <div
          v-for="v in vendors"
          :key="v"
          class="vendor-item"
          :class="{ active: selectedVendor === v }"
          @click="selectedVendor = v"
        >
          <span class="vendor-name">{{ v }}</span>
          <span class="vendor-count">{{ vendorCounts[v] || 0 }}</span>
        </div>
        <div
          class="vendor-item"
          :class="{ active: selectedVendor === '' }"
          @click="selectedVendor = ''"
        >
          <span class="vendor-name">All Vendors</span>
          <span class="vendor-count">{{ totalCount }}</span>
        </div>
      </div>

      <div class="attr-table-wrap">
        <table v-if="filtered.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Type</th>
              <th>Vendor</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in paginated" :key="a.vendor + '-' + a.id">
              <td class="mono">{{ a.vendor_id > 0 ? a.vendor_id + '.' + a.id : a.id }}</td>
              <td class="mono">{{ a.name }}</td>
              <td><code>{{ a.type }}</code></td>
              <td>{{ a.vendor }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">No attributes found</div>
        <div class="pagination" v-if="pages > 1">
          <button :disabled="page <= 1" @click="page--">◀</button>
          <span>Page {{ page }} / {{ pages }}</span>
          <button :disabled="page >= pages" @click="page++">▶</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const query = ref('')
const selectedVendor = ref('')
const vendors = ref([])
const vendorCounts = reactive({})
const allAttributes = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = 30

const filtered = computed(() => {
  let result = allAttributes.value
  if (selectedVendor.value) {
    result = result.filter(a => a.vendor === selectedVendor.value)
  }
  if (query.value) {
    const q = query.value.toLowerCase()
    result = result.filter(a => a.name.toLowerCase().includes(q) || a.vendor.toLowerCase().includes(q))
  }
  return result
})

const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const paginated = computed(() => {
  const start = (page.value - 1) * pageSize
  return filtered.value.slice(start, start + pageSize)
})

async function loadDictionary() {
  try {
    const res = await fetch('/api/dictionary')
    const data = await res.json()
    if (!data.success) return

    const attrs = []
    for (const [name, info] of Object.entries(data.attributes || {})) {
      attrs.push({ name, ...info })
    }
    attrs.sort((a, b) => a.name.localeCompare(b.name))
    allAttributes.value = attrs
    totalCount.value = data.count || attrs.length
    vendors.value = (data.vendors || []).sort()

    for (const a of attrs) {
      vendorCounts[a.vendor] = (vendorCounts[a.vendor] || 0) + 1
    }
  } catch (e) {
    console.error('Dictionary load error:', e)
  }
}

function search() {
  page.value = 1
}

onMounted(loadDictionary)
</script>

<style scoped>
.dictionary-section { display: flex; flex-direction: column; gap: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.section-header h2 { font-size: 18px; }
.search-bar { display: flex; align-items: center; gap: 12px; }
.search-bar input { padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; width: 240px; font-size: 14px; }
.count { color: #888; font-size: 13px; white-space: nowrap; }

.dict-layout { display: grid; grid-template-columns: 180px 1fr; gap: 20px; }
.vendor-list { display: flex; flex-direction: column; gap: 2px; }
.vendor-item { display: flex; justify-content: space-between; padding: 8px 12px; cursor: pointer; border-radius: 4px; font-size: 14px; }
.vendor-item:hover { background: #f0f4ff; }
.vendor-item.active { background: #3b82f6; color: #fff; }
.vendor-item.active .vendor-count { color: #bfdbfe; }
.vendor-count { color: #999; font-size: 12px; }

.attr-table-wrap { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
th { color: #666; font-weight: 600; text-transform: uppercase; font-size: 11px; }
.mono { font-family: monospace; font-size: 13px; }
code { background: #f0f0f0; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
.empty { text-align: center; color: #999; padding: 40px; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 16px; }
.pagination button { padding: 4px 12px; border: 1px solid #ddd; background: #fff; border-radius: 4px; cursor: pointer; }
.pagination button:disabled { opacity: 0.3; cursor: default; }
.pagination span { font-size: 13px; color: #666; }
</style>
