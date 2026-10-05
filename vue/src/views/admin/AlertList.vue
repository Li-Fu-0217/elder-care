<template>
  <div class="page-container">
    <div class="content-card">
      <div class="toolbar-row">
        <el-select v-model="status" clearable placeholder="状态" style="width: 140px">
          <el-option label="待处理" value="open" />
          <el-option label="处理中" value="handling" />
          <el-option label="已关闭" value="closed" />
        </el-select>
        <el-button type="primary" @click="loadData">查询</el-button>
      </div>
      <el-table v-loading="loading" :data="tableData" style="width: 100%" :header-cell-style="headerStyle">
        <el-table-column prop="elderName" label="老人" min-width="100" />
        <el-table-column prop="message" label="内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="location" label="位置" min-width="120" />
        <el-table-column prop="source" label="来源" width="90">
          <template #default="{ row }">{{ row.source === 'agent' ? 'Agent' : '手动' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="alertStatusTagType(row.status)" effect="light" size="small">
              {{ alertStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="warning" link @click="setStatus(row, 'handling')">处理中</el-button>
            <el-button type="success" link @click="setStatus(row, 'closed')">关闭</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="page.current"
          v-model:page-size="page.size"
          :total="page.total"
          background
          layout="total, prev, pager, next"
          small
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'AlertList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminAlerts, updateAlert } from '@/api/community'
import { formatDateTime, alertStatusLabel, alertStatusTagType } from '@/utils/format'

import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const loading = ref(false)
const tableData = ref([])
const status = ref('')
const page = reactive({ current: 1, size: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const data = await getAdminAlerts({
      current: page.current,
      size: page.size,
      status: status.value || undefined
    })
    tableData.value = data.records || []
    page.total = data.total || 0
  } finally {
    loading.value = false
  }
}

async function setStatus(row, next) {
  await updateAlert(row.id, { status: next })
  ElMessage.success('已更新')
  loadData()
}

onMounted(loadData)
</script>
