<template>
  <div class="page-container">
    <div class="content-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="活动列表" name="list">
          <div class="toolbar-row">
            <el-input
              v-model="keyword"
              class="search-input"
              placeholder="搜索标题 / 地点"
              clearable
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <span class="toolbar-spacer" />
            <el-button type="primary" @click="openDialog()">发布活动</el-button>
          </div>
          <el-table v-loading="loading" :data="tableData" style="width: 100%" :header-cell-style="headerStyle">
            <el-table-column prop="title" label="标题" min-width="160" />
            <el-table-column prop="location" label="地点" min-width="120" />
            <el-table-column prop="startTime" label="开始时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.startTime) }}</template>
            </el-table-column>
            <el-table-column label="名额" width="110">
              <template #default="{ row }">
                {{ row.registeredCount }}/{{ row.capacity ?? '不限' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '报名中' : '下架' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
                <el-button type="danger" link @click="remove(row)">删除</el-button>
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
        </el-tab-pane>
        <el-tab-pane label="报名记录" name="regs">
          <el-table :data="regs" style="width: 100%" :header-cell-style="headerStyle">
            <el-table-column prop="activityTitle" label="活动" min-width="160" />
            <el-table-column prop="elderName" label="老人" min-width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="registrationStatusTagType(row.status)" effect="light" size="small">
                  {{ registrationStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="报名时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.createTime) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="visible" :title="editId ? '编辑活动' : '发布活动'" width="520px" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="地点"><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="开始时间" required>
          <el-date-picker v-model="form.startTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="form.endTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="名额"><el-input-number v-model="form.capacity" :min="1" /></el-form-item>
        <el-form-item label="详情"><el-input v-model="form.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="上架"><el-switch v-model="form.status" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'ActivityList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminActivities,
  createActivity,
  updateActivity,
  deleteActivity,
  getAdminRegistrations
} from '@/api/community'
import { formatDateTime, registrationStatusLabel, registrationStatusTagType } from '@/utils/format'

import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const tab = ref('list')
const loading = ref(false)
const tableData = ref([])
const regs = ref([])
const keyword = ref('')
const page = reactive({ current: 1, size: 10, total: 0 })
const visible = ref(false)
const editId = ref(null)
const form = reactive({
  title: '',
  content: '',
  location: '',
  startTime: '',
  endTime: '',
  capacity: 30,
  status: 1
})

async function loadData() {
  loading.value = true
  try {
    const data = await getAdminActivities({
      current: page.current,
      size: page.size,
      keyword: keyword.value || undefined
    })
    tableData.value = data.records || []
    page.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.current = 1
  loadData()
}

function handleReset() {
  keyword.value = ''
  handleSearch()
}

async function loadRegs() {
  const data = await getAdminRegistrations({ current: 1, size: 50 })
  regs.value = data.records || []
}

function openDialog(row) {
  editId.value = row?.id ?? null
  Object.assign(form, {
    title: row?.title || '',
    content: row?.content || '',
    location: row?.location || '',
    startTime: row?.startTime || '',
    endTime: row?.endTime || '',
    capacity: row?.capacity ?? 30,
    status: row?.status ?? 1
  })
  visible.value = true
}

async function save() {
  if (!form.title || !form.startTime) {
    ElMessage.warning('请填写标题与开始时间')
    return
  }
  if (editId.value) await updateActivity(editId.value, form)
  else await createActivity(form)
  ElMessage.success('保存成功')
  visible.value = false
  loadData()
}

async function remove(row) {
  await ElMessageBox.confirm(`删除活动「${row.title}」？`, '提示', { type: 'warning' })
  await deleteActivity(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(() => {
  loadData()
  loadRegs()
})
</script>
