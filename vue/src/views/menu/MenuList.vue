<template>
  <div class="page-container">
    <div class="content-card">
      <div class="toolbar-row">
        <el-input
          v-model="keyword"
          class="search-input"
          placeholder="搜索名称 / 路径 / 图标"
          clearable
          :prefix-icon="Search"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        <span class="toolbar-spacer" />
        <el-button type="primary" :icon="Plus" @click="openDialog()">新增菜单</el-button>
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
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="path" label="路由路径" min-width="180" show-overflow-tooltip />
        <el-table-column prop="icon" label="图标" width="72">
          <template #default="{ row }">
            <el-tooltip v-if="row.icon" :content="row.icon" placement="top">
              <el-icon :size="20" class="menu-icon-cell">
                <component :is="resolveIcon(row.icon)" />
              </el-icon>
            </el-tooltip>
            <span v-else class="icon-empty">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sortOrder" label="排序" width="72" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button v-auth="'ADMIN'" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="560px"
      destroy-on-close
      align-center
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px">
        <el-form-item label="菜单名称" prop="name">
          <el-input v-model="form.name" placeholder="如：用户管理" />
        </el-form-item>
        <el-form-item label="路由路径" prop="path">
          <el-input v-model="form.path" placeholder="/admin/users" />
        </el-form-item>
        <el-form-item label="父菜单" prop="parentId">
          <el-select v-model="form.parentId" placeholder="顶级菜单" style="width: 100%">
            <el-option label="顶级（无父级）" :value="0" />
            <el-option
              v-for="item in parentOptions"
              :key="item.id"
              :label="`${item.name}（${item.path}）`"
              :value="item.id"
              :disabled="item.id === editingId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <IconPicker v-model="form.icon" />
        </el-form-item>
        <el-form-item label="排序" prop="sortOrder">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'MenuList' })

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search, Refresh } from '@element-plus/icons-vue'
import IconPicker from '@/components/IconPicker.vue'
import { resolveIcon } from '@/utils/icon'
import { getMenuManageList, createMenu, updateMenu, deleteMenu, deleteMenus } from '@/api/menu'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const parentMenuList = ref([])
const keyword = ref('')
const selectedRows = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const editingId = ref(null)

const defaultForm = () => ({
  name: '',
  path: '',
  parentId: 0,
  icon: '',
  sortOrder: 0
})

const form = reactive(defaultForm())

const formRules = {
  name: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  path: [
    { required: true, message: '请输入路由路径', trigger: 'blur' },
    {
      pattern: /^\/admin\/[a-zA-Z0-9/_-]+$/,
      message: '路径须以 /admin/ 开头',
      trigger: 'blur'
    }
  ],
  sortOrder: [{ required: true, message: '请输入排序', trigger: 'change' }]
}

const isEdit = computed(() => editingId.value !== null)
const dialogTitle = computed(() => (isEdit.value ? '编辑菜单' : '新增菜单'))

const parentOptions = computed(() =>
  parentMenuList.value.filter((m) => m.parentId === 0 || m.parentId === null)
)

async function loadParentMenuList() {
  parentMenuList.value = await getMenuManageList()
}

async function loadData() {
  loading.value = true
  try {
    tableData.value = await getMenuManageList({
      keyword: keyword.value || undefined
    })
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  selectedRows.value = []
  loadData()
}

function handleReset() {
  keyword.value = ''
  selectedRows.value = []
  loadData()
}

async function openDialog(row) {
  await loadParentMenuList()
  if (row) {
    editingId.value = row.id
    Object.assign(form, {
      name: row.name,
      path: row.path,
      parentId: row.parentId ?? 0,
      icon: row.icon || '',
      sortOrder: row.sortOrder ?? 0
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
      name: form.name,
      path: form.path,
      parentId: form.parentId,
      icon: form.icon || null,
      sortOrder: form.sortOrder
    }
    if (isEdit.value) {
      await updateMenu(editingId.value, payload)
      ElMessage.success('更新成功，重新登录或刷新后侧栏生效')
    } else {
      await createMenu(payload)
      ElMessage.success('创建成功，重新登录后侧栏与路由生效')
    }
    dialogVisible.value = false
    await loadParentMenuList()
    loadData()
  } finally {
    submitLoading.value = false
  }
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除菜单「${row.name}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteMenu(row.id)
  ElMessage.success('删除成功')
  await loadParentMenuList()
  loadData()
}

async function handleBatchDelete() {
  const rows = selectedRows.value
  if (!rows.length) {
    return
  }
  await ElMessageBox.confirm(`确定删除选中的 ${rows.length} 条菜单吗？内置菜单无法删除。`, '批量删除', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteMenus(rows.map((r) => r.id))
  ElMessage.success('批量删除成功')
  selectedRows.value = []
  await loadParentMenuList()
  loadData()
}

onMounted(() => {
  loadParentMenuList()
  loadData()
})
</script>

<style scoped>
.menu-icon-cell {
  color: var(--app-primary);
  vertical-align: middle;
}

.icon-empty {
  color: var(--app-text-secondary);
}

</style>
