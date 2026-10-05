<template>
  <div class="front-page med-page">
    <div class="front-shell">
      <section class="page-head">
        <h1>服药打卡</h1>
        <p>查看待服与漏服记录，一键标记已服</p>
      </section>

      <div class="med-toolbar">
        <el-select v-model="elderId" clearable placeholder="全部绑定老人" class="med-field" @change="handleSearch">
          <el-option v-for="e in elders" :key="e.id" :label="e.name" :value="e.id" />
        </el-select>
        <el-select v-model="statusFilter" clearable placeholder="状态" class="med-field med-field--sm" @change="handleSearch">
          <el-option label="待服" :value="2" />
          <el-option label="漏服" :value="0" />
          <el-option label="已服" :value="1" />
        </el-select>
        <el-button type="primary" round @click="handleSearch">查询</el-button>
        <el-button round @click="handleReset">重置</el-button>
        <span class="med-toolbar__spacer" />
        <el-button round @click="$router.push('/user/care')">关怀看板</el-button>
        <el-button type="primary" plain round @click="$router.push('/user/agent')">智能助手</el-button>
      </div>

      <div class="med-card" v-loading="loading">
        <el-empty
          v-if="!loading && !logs.length"
          :description="emptyText"
          :image-size="72"
        />
        <div v-for="row in logs" :key="row.id" class="med-row">
          <div class="med-row__main">
            <div class="med-row__title">
              <span class="med-row__drug">{{ row.drugName || '药品' }}</span>
              <el-tag :type="medicationStatusTagType(row.status)" effect="light" round size="small">
                {{ medicationStatusLabel(row.status) }}
              </el-tag>
            </div>
            <div class="med-row__meta">
              <span>{{ row.elderName || '-' }}</span>
              <span>计划 {{ formatDateTime(row.plannedTime) }}</span>
              <span v-if="row.takenTime">实际 {{ formatDateTime(row.takenTime) }}</span>
            </div>
          </div>
          <div class="med-row__actions">
            <el-button
              v-if="row.status !== 1"
              type="primary"
              round
              size="small"
              :loading="markingId === row.id"
              @click="markTaken(row)"
            >
              标记已服
            </el-button>
            <span v-else class="med-row__done">已记录</span>
          </div>
        </div>

        <div v-if="page.total > page.size" class="med-footer">
          <el-pagination
            v-model:current-page="page.current"
            v-model:page-size="page.size"
            :total="page.total"
            background
            layout="total, prev, pager, next"
            small
            @current-change="loadLogs"
          />
        </div>
      </div>

      <aside class="med-tips">
        <h3>打卡说明</h3>
        <ul>
          <li>待服：计划时间将至或当天待完成的服药</li>
          <li>漏服：超过计划时间仍未标记的记录</li>
          <li>标记已服后不可撤销，请按实际服用情况操作</li>
          <li>也可让智能助手帮您查询近期漏服情况</li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'UserMedications' })

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyElders } from '@/api/elder'
import { getMedicationLogs, markMedicationTaken } from '@/api/medication'
import {
  formatDateTime,
  medicationStatusLabel,
  medicationStatusTagType
} from '@/utils/format'

const elders = ref([])
const eldersReady = ref(false)
const elderId = ref(null)
const statusFilter = ref(null)
const loading = ref(false)
const markingId = ref(null)
const logs = ref([])
const page = reactive({ current: 1, size: 10, total: 0 })

const emptyText = computed(() => {
  if (!eldersReady.value) return '加载中…'
  if (!elders.value.length) return '请先在关怀看板绑定老人'
  if (statusFilter.value === 2) return '暂无待打卡记录'
  if (statusFilter.value === 0) return '暂无漏服记录'
  if (statusFilter.value === 1) return '暂无已服记录'
  return '暂无用药记录'
})

async function loadLogs() {
  if (!eldersReady.value) return
  if (!elders.value.length) {
    logs.value = []
    page.total = 0
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await getMedicationLogs({
      current: page.current,
      size: page.size,
      elderId: elderId.value || undefined,
      status: statusFilter.value === null || statusFilter.value === '' ? undefined : statusFilter.value
    })
    logs.value = data.records || []
    page.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.current = 1
  loadLogs()
}

function handleReset() {
  elderId.value = null
  statusFilter.value = null
  handleSearch()
}

async function markTaken(row) {
  markingId.value = row.id
  try {
    await markMedicationTaken(row.id)
    ElMessage.success('已记录服药')
    await loadLogs()
  } finally {
    markingId.value = null
  }
}

onMounted(async () => {
  loading.value = true
  try {
    elders.value = (await getMyElders()) || []
  } finally {
    eldersReady.value = true
  }
  // 默认优先看待服；若无记录则展示全部
  statusFilter.value = 2
  await loadLogs()
  if (!logs.value.length) {
    statusFilter.value = null
    await loadLogs()
  }
})
</script>

<style scoped>
.med-page {
  padding: 28px 0 48px;
}

.page-head {
  margin: 0 0 18px;
}

.page-head h1 {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 700;
  color: var(--care-ink, #1e2a24);
}

.page-head p {
  margin: 0;
  font-size: 14px;
  color: var(--care-muted, #5f6f66);
}

.med-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.med-field {
  width: 180px;
}

.med-field--sm {
  width: 120px;
}

.med-toolbar__spacer {
  flex: 1;
}

.med-card {
  background: #fff;
  border-radius: 16px;
  padding: 4px 8px;
  box-shadow: 0 8px 28px rgba(26, 46, 34, 0.06);
}

.med-card :deep(.el-empty) {
  padding: 36px 0;
}

.med-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid #eef4f0;
}

.med-row:last-of-type {
  border-bottom: none;
}

.med-row__title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.med-row__drug {
  font-size: 16px;
  font-weight: 600;
  color: #1e2a24;
}

.med-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  font-size: 13px;
  color: #6b7c72;
}

.med-row__done {
  font-size: 13px;
  color: #2f9b6a;
  font-weight: 500;
}

.med-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px 8px;
}

.med-tips {
  margin-top: 20px;
  padding: 18px 20px;
  border-radius: 16px;
  background: rgba(47, 155, 106, 0.06);
}

.med-tips h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #1e2a24;
}

.med-tips ul {
  margin: 0;
  padding-left: 18px;
  color: #5f6f66;
  font-size: 13px;
  line-height: 1.8;
}

@media (max-width: 720px) {
  .med-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .med-field,
  .med-field--sm {
    width: 100%;
  }
}
</style>
