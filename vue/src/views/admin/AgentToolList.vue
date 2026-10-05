<template>
  <div class="page-container agent-tools-page">
    <div class="content-card tools-intro">
      <h2 class="tools-intro__title">Agent 工具说明</h2>
      <p class="tools-intro__desc">
        智能助手通过下列业务工具读写养老数据。工具与
        <code>elder_service</code> /
        <code>knowledge_service</code>
        共用同一套权限与校验；每次调用写入「Agent 日志」。
      </p>
    </div>

    <div v-loading="loading" class="tools-grid">
      <el-empty v-if="!loading && !tools.length" description="暂无工具定义" />
      <div v-for="tool in tools" :key="tool.name" class="tool-card">
        <div class="tool-card__head">
          <div class="tool-card__title-row">
            <span class="tool-card__label">{{ tool.label }}</span>
            <code class="tool-card__name">{{ tool.name }}</code>
          </div>
          <div class="tool-card__tags">
            <el-tag size="small" effect="plain">{{ tool.category }}</el-tag>
            <el-tag
              size="small"
              :type="tool.sideEffect === '写库' ? 'warning' : 'success'"
              effect="light"
            >
              {{ tool.sideEffect }}
            </el-tag>
          </div>
        </div>
        <p class="tool-card__summary">{{ tool.summary }}</p>

        <div class="tool-card__section">
          <div class="tool-card__section-title">入参</div>
          <el-table :data="tool.params || []" size="small" :header-cell-style="headerStyle">
            <el-table-column prop="name" label="参数" width="120" />
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column label="必填" width="70">
              <template #default="{ row }">{{ row.required ? '是' : '否' }}</template>
            </el-table-column>
            <el-table-column prop="desc" label="说明" min-width="160" />
          </el-table>
        </div>

        <div class="tool-card__section">
          <div class="tool-card__section-title">使用规则</div>
          <ul class="tool-card__rules">
            <li v-for="(rule, i) in tool.rules || []" :key="i">{{ rule }}</li>
          </ul>
        </div>

        <div v-if="tool.examples?.length" class="tool-card__section">
          <div class="tool-card__section-title">示例说法</div>
          <div class="tool-card__examples">
            <el-tag
              v-for="(ex, i) in tool.examples"
              :key="i"
              round
              effect="plain"
              class="tool-card__ex"
            >
              {{ ex }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 管理端 Agent 工具说明：展示各工具用途、入参与调用规则（只读目录）。
 */
defineOptions({ name: 'AgentToolList' })

import { ref, onMounted } from 'vue'
import { getAgentTools } from '@/api/care'
import { TABLE_HEADER_STYLE } from '@/utils/tableStyle'

const headerStyle = TABLE_HEADER_STYLE
const loading = ref(false)
const tools = ref([])

async function loadData() {
  loading.value = true
  try {
    tools.value = (await getAgentTools()) || []
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.agent-tools-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tools-intro__title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.tools-intro__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #64748b;
}

.tools-intro__desc code {
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f1f5f9;
  color: #334155;
}

.tools-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 120px;
}

.tool-card {
  background: #fff;
  border: 1px solid var(--app-border, #e2e8f0);
  border-radius: 12px;
  padding: 18px 20px;
}

.tool-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.tool-card__title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-width: 0;
}

.tool-card__label {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.tool-card__name {
  display: inline-flex;
  align-items: center;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #047857;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 4px 12px;
  border-radius: 8px;
  line-height: 1.3;
}

.tool-card__tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.tool-card__summary {
  margin: 0 0 14px;
  font-size: 14px;
  line-height: 1.65;
  color: #334155;
}

.tool-card__section {
  margin-top: 12px;
}

.tool-card__section-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.tool-card__rules {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  font-size: 13px;
  line-height: 1.75;
}

.tool-card__examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tool-card__ex {
  max-width: 100%;
}
</style>
