<template>
  <div class="page-container">
    <div class="content-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="预约记录" name="bookings">
          <div class="toolbar-row">
            <el-select v-model="statusFilter" clearable placeholder="状态" style="width: 140px">
              <el-option label="待确认" value="pending" />
              <el-option label="已确认" value="confirmed" />
              <el-option label="已取消" value="cancelled" />
              <el-option label="已完成" value="done" />
            </el-select>
            <el-button type="primary" @click="loadBookings">查询</el-button>
          </div>
          <el-table v-loading="loading" :data="bookings" style="width: 100%" :header-cell-style="headerStyle">
            <el-table-column prop="elderName" label="老人" min-width="100" />
            <el-table-column prop="catalogName" label="服务" min-width="120" />
            <el-table-column prop="bookingTime" label="预约时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.bookingTime) }}</template>
            </el-table-column>
            <el-table-column prop="source" label="来源" min-width="90">
              <template #default="{ row }">{{ row.source === 'agent' ? 'Agent' : '手动' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" min-width="100">
              <template #default="{ row }">
                <el-tag :type="bookingStatusTagType(row.status)" effect="light" size="small">
                  {{ bookingStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button type="primary" link @click="setStatus(row, 'confirmed')">确认</el-button>
                <el-button type="success" link @click="setStatus(row, 'done')">完成</el-button>
                <el-button type="danger" link @click="setStatus(row, 'cancelled')">取消</el-button>
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
              @current-change="loadBookings"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="服务目录" name="catalog">
          <div class="toolbar-row">
            <span class="toolbar-spacer" />
            <el-button type="primary" @click="openCatalog()">新增服务</el-button>
          </div>
          <el-table :data="catalogs" style="width: 100%" :header-cell-style="headerStyle">
            <el-table-column prop="name" label="名称" min-width="140" />
            <el-table-column prop="serviceType" label="类型" min-width="140" />
            <el-table-column prop="durationMinutes" label="时长(分)" min-width="100" />
            <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link @click="openCatalog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="catVisible" :title="catId ? '编辑服务' : '新增服务'" width="480px">
      <el-form :model="catForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="catForm.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="catForm.serviceType" style="width: 100%">
            <el-option label="体检 health_check" value="health_check" />
            <el-option label="护理 nursing" value="nursing" />
            <el-option label="家政 housekeeping" value="housekeeping" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长"><el-input-number v-model="catForm.durationMinutes" :min="15" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="catForm.description" type="textarea" /></el-form-item>
        <el-form-item label="上架">
          <el-switch v-model="catForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="catVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCatalog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'BookingList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getAdminBookings,
  updateBooking,
  getAdminServiceCatalog,
  createServiceCatalog,
  updateServiceCatalog
} from '@/api/service'
import { formatDateTime, bookingStatusLabel, bookingStatusTagType } from '@/utils/format'

import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const tab = ref('bookings')
const loading = ref(false)
const bookings = ref([])
const catalogs = ref([])
const statusFilter = ref('')
const page = reactive({ current: 1, size: 10, total: 0 })

const catVisible = ref(false)
const catId = ref(null)
const catForm = reactive({
  name: '',
  serviceType: 'health_check',
  description: '',
  durationMinutes: 60,
  status: 1
})

async function loadBookings() {
  loading.value = true
  try {
    const data = await getAdminBookings({
      current: page.current,
      size: page.size,
      status: statusFilter.value || undefined
    })
    bookings.value = data.records || []
    page.total = data.total || 0
  } finally {
    loading.value = false
  }
}

async function setStatus(row, status) {
  await updateBooking(row.id, { status })
  ElMessage.success('已更新')
  loadBookings()
}

async function loadCatalog() {
  const data = await getAdminServiceCatalog({ current: 1, size: 50 })
  catalogs.value = data.records || []
}

function openCatalog(row) {
  catId.value = row?.id ?? null
  Object.assign(catForm, {
    name: row?.name || '',
    serviceType: row?.serviceType || 'health_check',
    description: row?.description || '',
    durationMinutes: row?.durationMinutes || 60,
    status: row?.status ?? 1
  })
  catVisible.value = true
}

async function saveCatalog() {
  if (catId.value) await updateServiceCatalog(catId.value, catForm)
  else await createServiceCatalog(catForm)
  ElMessage.success('保存成功')
  catVisible.value = false
  loadCatalog()
}

onMounted(() => {
  loadBookings()
  loadCatalog()
})
</script>
