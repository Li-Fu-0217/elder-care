<template>
  <div class="page-container">
    <div class="content-card">
      <div class="toolbar-row">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="搜索用户名 / 昵称 / 邮箱"
          clearable
          :prefix-icon="Search"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        <span class="toolbar-spacer" />
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增用户</el-button>
        <el-button
          type="danger"
          :icon="Delete"
          :disabled="!selectedRows.length"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        class="user-table"
        :header-cell-style="tableHeaderStyle"
        empty-text="暂无用户数据"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="用户" min-width="160">
          <template #default="{ row }">
            <div class="user-cell">
              <UserAvatar :user="row" :size="32" avatar-class="user-cell__avatar" />
              <div>
                <div class="user-cell__name">{{ row.nickname || row.username }}</div>
                <div class="user-cell__sub">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="132">
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="96">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" effect="light" round size="small">
              {{ roleLabel(row.role, roleOptions) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" effect="light" round size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="176">
          <template #default="{ row }">
            <span class="time-text">{{ formatDateTime(row.createTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="520px"
      destroy-on-close
      align-center
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px" label-position="right">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="3-50 个字符" />
        </el-form-item>
        <el-form-item :label="isEdit ? '新密码' : '密码'" :prop="isEdit ? '' : 'password'">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="isEdit ? '不修改请留空' : '至少 3 个字符'"
            show-password
          />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="选填" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="example@mail.com" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="11 位手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio v-for="item in roleOptions" :key="item.code" :label="item.code">
              {{ item.name }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'UserList' })

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Delete } from '@element-plus/icons-vue'
import { getUserPage, createUser, updateUser, deleteUser, deleteUsers } from '@/api/user'
import { getRoleList } from '@/api/role'
import { formatDateTime, roleLabel, roleTagType, statusLabel } from '@/utils/format'
import UserAvatar from '@/components/UserAvatar.vue'

const loading = ref(false)
const roleOptions = ref([])
const submitLoading = ref(false)
const tableData = ref([])
const keyword = ref('')
const selectedRows = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const editingId = ref(null)

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const tableHeaderStyle = {
  background: '#f8fafc',
  color: '#475569',
  fontWeight: '600'
}

const defaultForm = () => ({
  username: '',
  password: '',
  nickname: '',
  email: '',
  phone: '',
  role: 'USER',
  status: 1
})

const form = reactive(defaultForm())

const isEdit = computed(() => editingId.value !== null)
const dialogTitle = computed(() => (isEdit.value ? '编辑用户' : '新增用户'))

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度为 3-50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 3, max: 50, message: '长度为 3-50 个字符', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const data = await getUserPage({
      current: pagination.current,
      size: pagination.size,
      keyword: keyword.value || undefined
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

function handleReset() {
  keyword.value = ''
  pagination.current = 1
  selectedRows.value = []
  loadData()
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    Object.assign(form, {
      username: row.username,
      password: '',
      nickname: row.nickname,
      email: row.email,
      phone: row.phone,
      role: row.role,
      status: row.status
    })
  } else {
    editingId.value = null
    Object.assign(form, defaultForm())
  }
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(form, defaultForm())
  editingId.value = null
}

async function handleSubmit() {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    const payload = {
      username: form.username,
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
      role: form.role,
      status: form.status
    }
    if (form.password) {
      payload.password = form.password
    }
    if (isEdit.value) {
      await updateUser(editingId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await createUser(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除用户「${row.nickname || row.username}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleBatchDelete() {
  const rows = selectedRows.value
  if (!rows.length) {
    return
  }
  await ElMessageBox.confirm(`确定删除选中的 ${rows.length} 个用户吗？`, '批量删除', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteUsers(rows.map((r) => r.id))
  ElMessage.success('批量删除成功')
  selectedRows.value = []
  loadData()
}

onMounted(async () => {
  roleOptions.value = await getRoleList()
  loadData()
})
</script>

<style scoped>
.user-table {
  width: 100%;
}

.user-table :deep(.el-table__empty-block) {
  min-height: 80px;
}

.user-table :deep(.el-table__body td:last-child .cell),
.user-table :deep(.el-table__header th:last-child .cell) {
  overflow: visible;
}

</style>
