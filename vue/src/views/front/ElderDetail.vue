<template>
  <div class="front-page elder-detail-page">
    <div class="front-shell">
      <el-page-header @back="$router.push('/user/care')" content="老人档案" />
      <div v-loading="loading" class="detail-card" v-if="elder">
        <h1>{{ elder.name }}</h1>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="性别">{{ elder.gender === 1 ? '男' : '女' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ elder.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="住址" :span="2">{{ elder.address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="慢性病" :span="2">{{ elder.chronicDiseases || '-' }}</el-descriptions-item>
          <el-descriptions-item label="当前用药" :span="2">{{ elder.currentMedications || '-' }}</el-descriptions-item>
          <el-descriptions-item label="健康摘要" :span="2">{{ elder.healthSummary || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h2 class="section-title">近 3 天漏服</h2>
        <el-table :data="health?.recentMissedLogs || []" empty-text="无漏服记录" style="width: 100%">
          <el-table-column prop="drugName" label="药品" min-width="120" />
          <el-table-column prop="plannedTime" label="计划时间" min-width="180">
            <template #default="{ row }">{{ formatDateTime(row.plannedTime) }}</template>
          </el-table-column>
        </el-table>

        <h2 class="section-title">用药计划</h2>
        <el-table :data="schedules" empty-text="暂无计划" style="width: 100%">
          <el-table-column prop="drugName" label="药品" min-width="120" />
          <el-table-column prop="dosage" label="剂量" min-width="100" />
          <el-table-column prop="scheduleTimes" label="时间" min-width="140" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ElderDetail' })

import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getElderById, getElderHealth } from '@/api/elder'
import { getMedicationSchedules } from '@/api/medication'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const loading = ref(false)
const elder = ref(null)
const health = ref(null)
const schedules = ref([])

onMounted(async () => {
  const id = Number(route.params.id)
  loading.value = true
  try {
    elder.value = await getElderById(id)
    health.value = await getElderHealth(id)
    schedules.value = (await getMedicationSchedules({ elderId: id })) || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.elder-detail-page {
  padding: 28px 0 48px;
}
.detail-card {
  margin-top: 20px;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--care-line);
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.05);
}
.detail-card h1 {
  margin: 0 0 16px;
  font-size: 24px;
  font-weight: 800;
  color: var(--care-ink);
}
.section-title {
  margin: 24px 0 12px;
  font-size: 16px;
}
</style>
