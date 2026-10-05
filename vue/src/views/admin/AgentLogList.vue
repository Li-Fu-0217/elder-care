<template>
  <div class="page-container agent-log-page">
    <div class="content-card log-intro">
      <h2 class="log-intro__title">Agent 调用日志</h2>
      <p class="log-intro__desc">
        这里记录智能助手<strong>每一次调用业务工具</strong>的痕迹：调用了哪个工具、传了什么参数、返回了什么结果，
        便于运维排查与审计。工具含义见侧栏
        <router-link class="log-intro__link" to="/admin/agent-tools">Agent 工具</router-link>
        。
      </p>
    </div>

    <div class="content-card">
      <div class="toolbar-row">
        <el-select
          v-model="toolName"
          clearable
          filterable
          placeholder="按工具筛选"
          style="width: 220px"
        >
          <el-option
            v-for="(label, name) in AGENT_TOOL_LABELS"
            :key="name"
            :label="label"
            :value="name"
          />
        </el-select>
        <el-input
          v-model="sessionId"
          placeholder="会话 ID（可选）"
          clearable
          style="width: 260px"
        />
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        :header-cell-style="headerStyle"
        empty-text="暂无工具调用记录（用户在前台使用智能助手后会出现）"
        @row-click="openDetail"
      >
        <el-table-column label="做了什么" min-width="160">
          <template #default="{ row }">
            <div class="tool-cell">
              <span class="tool-cell__label">{{ agentToolLabel(row.toolName) }}</span>
              <code class="tool-cell__code">{{ row.toolName }}</code>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="请求说明" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatToolArgs(row.toolName, row.requestArgs) }}
          </template>
        </el-table-column>
        <el-table-column label="执行结果" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatToolResult(row.toolName, row.responseData) }}
          </template>
        </el-table-column>
        <el-table-column prop="costMs" label="耗时" width="90">
          <template #default="{ row }">{{ row.costMs != null ? `${row.costMs} ms` : '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="88">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small" effect="light">
              {{ row.status === 1 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="" width="72" fixed="right">
          <template #default>
            <el-button type="primary" link>详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          background
          layout="total, prev, pager, next"
          small
          @current-change="loadData"
        />
      </div>
    </div>

    <el-drawer v-model="detailVisible" title="调用详情" size="420px" destroy-on-close>
      <template v-if="current">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="工具">
            {{ agentToolLabel(current.toolName) }}
            <code class="drawer-code">{{ current.toolName }}</code>
          </el-descriptions-item>
          <el-descriptions-item label="会话 ID">{{ current.sessionId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            {{ current.status === 1 ? '成功' : '失败' }}
          </el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ current.costMs != null ? `${current.costMs} ms` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="时间">
            {{ formatDateTime(current.createTime) }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="drawer-block">
          <div class="drawer-block__title">请求说明</div>
          <p>{{ formatToolArgs(current.toolName, current.requestArgs) }}</p>
          <pre class="drawer-pre">{{ prettyJson(current.requestArgs) }}</pre>
        </div>
        <div class="drawer-block">
          <div class="drawer-block__title">执行结果</div>
          <p>{{ formatToolResult(current.toolName, current.responseData) }}</p>
          <pre class="drawer-pre">{{ prettyJson(current.responseData) }}</pre>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
/**
 * Agent 工具调用日志：把每次 Function Calling 落库记录展示为可读说明，便于运维审计。
 */
defineOptions({ name: 'AgentLogList' })

import { ref, reactive, onMounted } from 'vue'
import { getAgentToolLogs } from '@/api/care'
import { formatDateTime } from '@/utils/format'
import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'
import {
  AGENT_TOOL_LABELS,
  agentToolLabel,
  formatToolArgs,
  formatToolResult
} from '@/utils/agentTools'

const headerStyle = TABLE_HEADER_STYLE
const loading = ref(false)
const tableData = ref([])
const toolName = ref('')
const sessionId = ref('')
const pagination = reactive({ current: 1, size: 10, total: 0 })
const detailVisible = ref(false)
const current = ref(null)

function prettyJson(raw) {
  if (raw == null || raw === '') return '-'
  try {
    const obj = typeof raw === 'string' ? JSON.parse(raw) : raw
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(raw)
  }
}

function openDetail(row) {
  current.value = row
  detailVisible.value = true
}

function handleSearch() {
  pagination.current = 1
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const data = await getAgentToolLogs({
      current: pagination.current,
      size: pagination.size,
      toolName: toolName.value || undefined,
      sessionId: sessionId.value || undefined
    })
    tableData.value = data.records || []
    pagination.total = data.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.agent-log-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.log-intro__title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.log-intro__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #64748b;
}

.log-intro__link {
  color: var(--el-color-primary);
  font-weight: 600;
  text-decoration: none;
}

.log-intro__link:hover {
  text-decoration: underline;
}

.tool-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-cell__label {
  font-weight: 600;
  color: #0f172a;
}

.tool-cell__code {
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  padding: 1px 6px;
  border-radius: 4px;
  width: fit-content;
}

:deep(.el-table__row) {
  cursor: pointer;
}

.drawer-code {
  margin-left: 8px;
  font-size: 12px;
  color: #047857;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 4px;
}

.drawer-block {
  margin-top: 16px;
}

.drawer-block__title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.drawer-block p {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
}

.drawer-pre {
  margin: 0;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #334155;
}
</style>
