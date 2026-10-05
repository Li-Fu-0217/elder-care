<template>
  <div class="page-container">
    <div class="content-card">
      <el-tabs v-model="logType" class="log-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="登录日志" name="login" />
        <el-tab-pane label="操作日志" name="operation" />
      </el-tabs>

      <div class="toolbar-row">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="按账号搜索"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <span class="toolbar-spacer" />
        <el-button
          type="danger"
          :disabled="!selectedRows.length"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="logTypeName" label="类型" width="72" />
        <el-table-column prop="username" label="账号" width="110" />
        <el-table-column v-if="logType === 'login'" prop="message" label="说明" min-width="160" show-overflow-tooltip />
        <template v-if="logType === 'operation'">
          <el-table-column prop="module" label="模块" width="100" />
          <el-table-column prop="action" label="操作" width="120" />
          <el-table-column prop="method" label="方式" width="70" />
          <el-table-column prop="url" label="地址" min-width="140" show-overflow-tooltip />
          <el-table-column prop="costMs" label="耗时(ms)" width="90" />
        </template>
        <el-table-column prop="ip" label="IP" width="148" show-overflow-tooltip />
        <el-table-column prop="status" label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small" effect="light">
              {{ row.status === 1 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="时间" width="176">
          <template #default="{ row }">
            <span class="time-text">{{ formatDateTime(row.createTime) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          background
          layout="total, sizes, prev, pager, next"
          small
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'SystemLogList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSystemLogs, deleteLogsBatch } from '@/api/log'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tableData = ref([])
const keyword = ref('')
const logType = ref('login')
const selectedRows = ref([])
const pagination = reactive({ current: 1, size: 10, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const data = await getSystemLogs({
      current: pagination.current,
      size: pagination.size,
      username: keyword.value || undefined,
      type: logType.value
    })
    tableData.value = data.records
    pagination.total = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
  selectedRows.value = []
  loadData()
}

function handleTabChange() {
  pagination.current = 1
  selectedRows.value = []
  loadData()
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

async function handleBatchDelete() {
  const rows = selectedRows.value
  if (!rows.length) {
    return
  }
  const typeLabel = logType.value === 'login' ? '登录日志' : '操作日志'
  await ElMessageBox.confirm(`确定删除选中的 ${rows.length} 条${typeLabel}吗？`, '批量删除', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteLogsBatch(
    logType.value,
    rows.map((r) => r.id)
  )
  ElMessage.success('批量删除成功')
  selectedRows.value = []
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.log-tabs {
  margin-bottom: 12px;
}
</style>
