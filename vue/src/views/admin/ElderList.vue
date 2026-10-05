<template>
  <div class="page-container">
    <div class="content-card">
      <div class="toolbar-row">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="搜索姓名 / 电话"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
        <span class="toolbar-spacer" />
        <el-button type="primary" @click="openDialog()">新增老人</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" style="width: 100%" :header-cell-style="headerStyle" empty-text="暂无数据">
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">{{ row.gender === 1 ? '男' : row.gender === 0 ? '女' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" min-width="130">
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="chronicDiseases" label="慢性病" min-width="160" show-overflow-tooltip />
        <el-table-column prop="emergencyContact" label="紧急联系人" min-width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" round>
              {{ row.status === 1 ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button type="primary" link @click="openFamily(row)">家属</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑老人' : '新增老人'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :label="1">男</el-radio>
            <el-radio :label="0">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birthDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="住址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="紧急联系人"><el-input v-model="form.emergencyContact" /></el-form-item>
        <el-form-item label="紧急电话"><el-input v-model="form.emergencyPhone" /></el-form-item>
        <el-form-item label="慢性病"><el-input v-model="form.chronicDiseases" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="当前用药"><el-input v-model="form.currentMedications" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="健康摘要"><el-input v-model="form.healthSummary" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="familyVisible" :title="`家属绑定 — ${familyElder?.name || ''}`" width="560px">
      <p class="family-tip">每位老人仅可绑定一位家属；已绑定需先解绑再更换。</p>
      <div v-loading="familyLoading" class="family-body">
        <template v-if="!familyLoading">
          <div v-if="!familyList.length" class="toolbar-row" style="margin-bottom: 12px">
            <el-select
              v-model="bindForm.userId"
              filterable
              clearable
              placeholder="选择子女用户"
              style="width: 240px"
            >
              <el-option
                v-for="u in userOptions"
                :key="u.id"
                :label="`${u.nickname || u.username}（${u.username}）`"
                :value="u.id"
              />
            </el-select>
            <el-input v-model="bindForm.relation" placeholder="关系" style="width: 100px" />
            <el-button type="primary" @click="handleBind">绑定</el-button>
          </div>
          <el-empty v-if="!familyList.length" description="暂未绑定家属" :image-size="64" />
          <el-table v-else :data="familyList" size="small">
            <el-table-column prop="username" label="账号" width="100" />
            <el-table-column prop="nickname" label="昵称" width="100" />
            <el-table-column prop="relation" label="关系" width="80" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="danger" link @click="handleUnbind(row)">解绑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 管理端老人档案：CRUD + 家属绑定（每位老人仅一位家属）。
 */
defineOptions({ name: 'ElderList' })

import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getElderPage,
  createElder,
  updateElder,
  deleteElder,
  listFamily,
  bindFamily,
  unbindFamily
} from '@/api/elder'
import { getUserPage } from '@/api/user'
import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const keyword = ref('')
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const pagination = reactive({ current: 1, size: 10, total: 0 })

const defaultForm = () => ({
  name: '',
  gender: 1,
  birthDate: null,
  phone: '',
  address: '',
  emergencyContact: '',
  emergencyPhone: '',
  chronicDiseases: '',
  currentMedications: '',
  healthSummary: '',
  status: 1
})
const form = reactive(defaultForm())
const rules = { name: [{ required: true, message: '请输入姓名', trigger: 'blur' }] }

const familyVisible = ref(false)
const familyLoading = ref(false)
const familyElder = ref(null)
const familyList = ref([])
const userOptions = ref([])
const bindForm = reactive({ userId: null, relation: '子女' })

async function loadUserOptions() {
  const data = await getUserPage({ current: 1, size: 200 })
  userOptions.value = (data.records || []).filter((u) => u.role === 'USER')
}

async function loadData() {
  loading.value = true
  try {
    const data = await getElderPage({
      current: pagination.current,
      size: pagination.size,
      keyword: keyword.value || undefined
    })
    tableData.value = data.records || []
    pagination.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
  loadData()
}

function handleReset() {
  keyword.value = ''
  handleSearch()
}

function openDialog(row) {
  editingId.value = row?.id ?? null
  Object.assign(form, defaultForm(), row || {})
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const payload = { ...form }
    if (editingId.value) await updateElder(editingId.value, payload)
    else await createElder(payload)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除「${row.name}」？`, '提示', { type: 'warning' })
  await deleteElder(row.id)
  ElMessage.success('已删除')
  loadData()
}

async function openFamily(row) {
  familyElder.value = row
  familyVisible.value = true
  familyLoading.value = true
  familyList.value = []
  bindForm.userId = null
  bindForm.relation = '子女'
  try {
    if (!userOptions.value.length) {
      await loadUserOptions()
    }
    familyList.value = (await listFamily({ elderId: row.id })) || []
  } finally {
    familyLoading.value = false
  }
}

async function handleBind() {
  if (!bindForm.userId) {
    ElMessage.warning('请选择子女用户')
    return
  }
  await bindFamily({
    userId: bindForm.userId,
    elderId: familyElder.value.id,
    relation: bindForm.relation,
    isPrimary: 1
  })
  ElMessage.success('绑定成功')
  bindForm.userId = null
  familyList.value = (await listFamily({ elderId: familyElder.value.id })) || []
}

async function handleUnbind(row) {
  await unbindFamily(row.id)
  ElMessage.success('已解绑')
  familyList.value = (await listFamily({ elderId: familyElder.value.id })) || []
}

onMounted(loadData)
</script>

<style scoped>
.family-body {
  min-height: 120px;
}

.family-tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary, #64748b);
}
</style>
