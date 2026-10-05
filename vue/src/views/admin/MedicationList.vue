<template>
  <div class="page-container">
    <div class="content-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="用药计划" name="schedule">
          <div class="toolbar-row">
            <el-select
              v-model="elderIdFilter"
              clearable
              filterable
              placeholder="选择老人"
              style="width: 200px"
            >
              <el-option
                v-for="e in elderOptions"
                :key="e.id"
                :label="elderLabel(e)"
                :value="e.id"
              />
            </el-select>
            <el-button type="primary" @click="loadSchedules">查询</el-button>
            <span class="toolbar-spacer" />
            <el-button type="primary" @click="openSchedule()">新增计划</el-button>
          </div>
          <el-table
            v-loading="loading"
            :data="schedules"
            class="full-width-table"
            style="width: 100%"
            :header-cell-style="headerStyle"
          >
            <el-table-column prop="elderName" label="老人" min-width="100" />
            <el-table-column prop="drugName" label="药品" min-width="120" />
            <el-table-column prop="dosage" label="剂量" min-width="90" />
            <el-table-column prop="scheduleTimes" label="服用时间" min-width="140" />
            <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button type="primary" link @click="openSchedule(row)">编辑</el-button>
                <el-button type="danger" link @click="removeSchedule(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="schedPage.current"
              v-model:page-size="schedPage.size"
              :total="schedPage.total"
              background
              layout="total, prev, pager, next"
              small
              @current-change="loadSchedules"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="用药记录 / 漏服" name="logs">
          <div class="toolbar-row">
            <el-select
              v-model="logElderId"
              clearable
              filterable
              placeholder="选择老人"
              style="width: 200px"
            >
              <el-option
                v-for="e in elderOptions"
                :key="e.id"
                :label="elderLabel(e)"
                :value="e.id"
              />
            </el-select>
            <el-select v-model="logStatus" clearable placeholder="状态" style="width: 120px">
              <el-option label="漏服" :value="0" />
              <el-option label="已服" :value="1" />
              <el-option label="待服" :value="2" />
            </el-select>
            <el-button type="primary" @click="loadLogs">查询</el-button>
          </div>
          <el-table
            v-loading="logLoading"
            :data="logs"
            class="full-width-table"
            style="width: 100%"
            :header-cell-style="headerStyle"
          >
            <el-table-column prop="elderName" label="老人" min-width="120" />
            <el-table-column prop="drugName" label="药品" min-width="140" />
            <el-table-column prop="plannedTime" label="计划时间" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.plannedTime) }}</template>
            </el-table-column>
            <el-table-column prop="takenTime" label="实际时间" min-width="180">
              <template #default="{ row }">{{ formatDateTime(row.takenTime) || '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" min-width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 0 ? 'danger' : row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 0 ? '漏服' : row.status === 1 ? '已服' : '待服' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="logPage.current"
              v-model:page-size="logPage.size"
              :total="logPage.total"
              background
              layout="total, prev, pager, next"
              small
              @current-change="loadLogs"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="schedVisible" :title="schedId ? '编辑计划' : '新增计划'" width="480px" destroy-on-close>
      <el-form :model="schedForm" label-width="100px">
        <el-form-item label="老人" required>
          <el-select
            v-model="schedForm.elderId"
            filterable
            placeholder="请选择老人"
            style="width: 100%"
          >
            <el-option
              v-for="e in elderOptions"
              :key="e.id"
              :label="elderLabel(e)"
              :value="e.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="药品" required>
          <el-input v-model="schedForm.drugName" />
        </el-form-item>
        <el-form-item label="剂量">
          <el-input v-model="schedForm.dosage" />
        </el-form-item>
        <el-form-item label="服用时间" required>
          <el-input v-model="schedForm.scheduleTimes" placeholder="如 08:00,20:00" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="schedForm.remark" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="schedForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="schedVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSchedule">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 管理端用药：计划 CRUD（选老人）+ 用药/漏服记录筛选。
 */
defineOptions({ name: 'MedicationList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMedicationSchedules,
  createMedicationSchedule,
  updateMedicationSchedule,
  deleteMedicationSchedule,
  getMedicationLogs
} from '@/api/medication'
import { getElderPage } from '@/api/elder'
import { formatDateTime } from '@/utils/format'
import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const activeTab = ref('schedule')
const loading = ref(false)
const logLoading = ref(false)
const schedules = ref([])
const logs = ref([])
const elderOptions = ref([])
const elderIdFilter = ref(undefined)
const logElderId = ref(undefined)
const logStatus = ref(undefined)
const schedPage = reactive({ current: 1, size: 10, total: 0 })
const logPage = reactive({ current: 1, size: 10, total: 0 })

const schedVisible = ref(false)
const schedId = ref(null)
const schedForm = reactive({
  elderId: null,
  drugName: '',
  dosage: '',
  scheduleTimes: '',
  remark: '',
  status: 1
})

function elderLabel(e) {
  const phone = e.phone ? `（${e.phone}）` : ''
  return `${e.name}${phone}`
}

async function loadElderOptions() {
  const data = await getElderPage({ current: 1, size: 200 })
  elderOptions.value = data.records || []
}

async function loadSchedules() {
  loading.value = true
  try {
    const data = await getMedicationSchedules({
      current: schedPage.current,
      size: schedPage.size,
      elderId: elderIdFilter.value || undefined
    })
    schedules.value = data.records || []
    schedPage.total = data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  logLoading.value = true
  try {
    const data = await getMedicationLogs({
      current: logPage.current,
      size: logPage.size,
      elderId: logElderId.value || undefined,
      status: logStatus.value
    })
    logs.value = data.records || []
    logPage.total = data.total || 0
  } finally {
    logLoading.value = false
  }
}

function openSchedule(row) {
  schedId.value = row?.id ?? null
  Object.assign(schedForm, {
    elderId: row?.elderId ?? null,
    drugName: row?.drugName || '',
    dosage: row?.dosage || '',
    scheduleTimes: row?.scheduleTimes || '',
    remark: row?.remark || '',
    status: row?.status ?? 1
  })
  schedVisible.value = true
}

async function saveSchedule() {
  if (!schedForm.elderId || !schedForm.drugName || !schedForm.scheduleTimes) {
    ElMessage.warning('请填写必填项')
    return
  }
  if (schedId.value) await updateMedicationSchedule(schedId.value, schedForm)
  else await createMedicationSchedule(schedForm)
  ElMessage.success('保存成功')
  schedVisible.value = false
  loadSchedules()
}

async function removeSchedule(row) {
  await ElMessageBox.confirm(`删除计划「${row.drugName}」？`, '提示', { type: 'warning' })
  await deleteMedicationSchedule(row.id)
  ElMessage.success('已删除')
  loadSchedules()
}

onMounted(async () => {
  await loadElderOptions()
  loadSchedules()
  loadLogs()
})
</script>
