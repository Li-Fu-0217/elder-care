<template>
  <div class="page-container">
    <div class="content-card">
      <div class="toolbar-row">
        <el-select v-model="filterType" clearable placeholder="文档类型" style="width: 140px">
          <el-option label="政策" value="policy" />
          <el-option label="用药" value="medication" />
          <el-option label="服务" value="service" />
        </el-select>
        <el-button type="primary" @click="loadData">查询</el-button>
        <span class="toolbar-spacer" />
        <el-button type="primary" @click="openUpload">上传文档</el-button>
      </div>
      <el-table v-loading="loading" :data="filteredRows" style="width: 100%" :header-cell-style="headerStyle">
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="docType" label="类型" width="100">
          <template #default="{ row }">{{ typeLabel(row.docType) }}</template>
        </el-table-column>
        <el-table-column prop="chunkCount" label="切片数" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="openChunks(row)">{{ row.chunkCount }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'" size="small">
              {{ row.status === 1 ? '已就绪' : '待向量化' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button type="primary" link @click="openChunks(row)">切片</el-button>
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
    </div>

    <el-dialog v-model="visible" title="上传知识库文档" width="480px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="默认取文件名" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.docType" style="width: 100%">
            <el-option label="政策" value="policy" />
            <el-option label="用药" value="medication" />
            <el-option label="服务" value="service" />
          </el-select>
        </el-form-item>
        <el-form-item label="文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".txt,.md,.markdown,.pdf"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 txt / md / pdf，上传后同步切片并写入向量库</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传并向量化</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="chunkVisible"
      :title="`切片详情 — ${chunkDoc?.title || ''}`"
      width="720px"
      destroy-on-close
      append-to-body
    >
      <div v-loading="chunkLoading" class="chunk-list">
        <el-empty v-if="!chunkLoading && !chunks.length" description="暂无切片" :image-size="72" />
        <div v-for="c in chunks" :key="c.id" class="chunk-item">
          <div class="chunk-item__head">
            <span class="chunk-item__index">切片 #{{ c.chunkIndex + 1 }}</span>
            <span class="chunk-item__meta">{{ c.content?.length || 0 }} 字</span>
          </div>
          <pre class="chunk-item__body">{{ c.content }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 管理端知识库：上传 txt/md/pdf → 切片 → Chroma 向量化；可查看切片。
 */
defineOptions({ name: 'KnowledgeList' })

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getKnowledgeDocuments,
  getKnowledgeChunks,
  uploadKnowledgeDocument,
  deleteKnowledgeDocument
} from '@/api/knowledge'
import { formatDateTime } from '@/utils/format'
import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const loading = ref(false)
const uploading = ref(false)
const tableData = ref([])
const filterType = ref('')
const page = reactive({ current: 1, size: 10, total: 0 })
const visible = ref(false)
const uploadRef = ref(null)
const form = reactive({ title: '', docType: 'policy', file: null })

const chunkVisible = ref(false)
const chunkLoading = ref(false)
const chunkDoc = ref(null)
const chunks = ref([])

const filteredRows = computed(() => {
  if (!filterType.value) return tableData.value
  return tableData.value.filter((r) => r.docType === filterType.value)
})

function typeLabel(t) {
  return { policy: '政策', medication: '用药', service: '服务' }[t] || t || '-'
}

async function loadData() {
  loading.value = true
  try {
    const data = await getKnowledgeDocuments({ current: page.current, size: page.size })
    tableData.value = data.records || []
    page.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function openUpload() {
  form.title = ''
  form.docType = 'policy'
  form.file = null
  visible.value = true
}

function onFileChange(file) {
  form.file = file?.raw || null
  const name = file?.name || file?.raw?.name || ''
  if (name) {
    form.title = name.replace(/\.(txt|md|markdown|pdf)$/i, '')
  }
}

function onFileRemove() {
  form.file = null
  form.title = ''
}

async function submitUpload() {
  if (!form.file) {
    ElMessage.warning('请选择文件')
    return
  }
  const fd = new FormData()
  fd.append('file', form.file)
  fd.append('title', form.title || '')
  fd.append('doc_type', form.docType)
  uploading.value = true
  try {
    await uploadKnowledgeDocument(fd)
    ElMessage.success('上传并向量化成功')
    visible.value = false
    await loadData()
  } finally {
    uploading.value = false
  }
}

async function openChunks(row) {
  chunkDoc.value = row
  chunkVisible.value = true
  chunkLoading.value = true
  chunks.value = []
  try {
    chunks.value = (await getKnowledgeChunks(row.id)) || []
  } finally {
    chunkLoading.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除「${row.title}」及其切片与向量？`, '提示', { type: 'warning' })
  await deleteKnowledgeDocument(row.id)
  ElMessage.success('已删除')
  await loadData()
}

onMounted(loadData)
</script>

<style scoped>
.chunk-list {
  max-height: 60vh;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chunk-item {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #f8fafc;
  padding: 12px 14px;
}

.chunk-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.chunk-item__index {
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
}

.chunk-item__meta {
  font-size: 12px;
  color: var(--app-text-secondary);
}

.chunk-item__body {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.65;
  color: #334155;
  font-family: inherit;
}
</style>
