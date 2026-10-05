<template>
  <div class="agent-steps" v-if="steps?.length">
    <div class="agent-steps__title">办理过程</div>
    <TransitionGroup name="step-fade" tag="div" class="agent-steps__list">
      <div
        v-for="(step, index) in visibleSteps"
        :key="`${step.round}-${index}-${step.action || 'think'}`"
        class="agent-steps__item"
        :class="{ 'is-tool': !!step.action }"
      >
        <div class="agent-steps__round">步骤 {{ step.round }}</div>
        <div v-if="step.thought" class="agent-steps__thought">
          <span class="label">分析</span>
          {{ step.thought }}
        </div>
        <div v-if="step.action" class="agent-steps__action">
          <span class="label">操作</span>
          <span class="agent-steps__tool">{{ toolLabel(step.action) }}</span>
        </div>
        <div v-if="step.observation" class="agent-steps__obs">
          <span class="label">结果</span>
          <span class="agent-steps__obs-text">{{ formatObservation(step) }}</span>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
defineOptions({ name: 'AgentThoughtSteps' })

import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  /** 逐步展示动画；false 则一次全部显示 */
  animate: { type: Boolean, default: true }
})

const TOOL_LABELS = {
  query_health_record: '查询健康档案',
  check_medication_schedule: '查询用药与漏服',
  query_available_service: '查询可预约时段',
  book_service: '提交服务预约',
  notify_family: '通知子女',
  trigger_emergency_alert: '触发紧急告警',
  query_knowledge_base: '检索知识库'
}

function toolLabel(name) {
  return TOOL_LABELS[name] || name
}

/** 前端兜底：若后端仍返回 JSON 字符串，转成可读摘要 */
function formatObservation(step) {
  const raw = String(step?.observation || '').trim()
  if (!raw) return ''
  if (!(raw.startsWith('{') || raw.startsWith('['))) return raw
  try {
    const data = JSON.parse(raw)
    const action = step?.action || ''
    if (action === 'book_service' || data.catalogName || data.catalog_name) {
      const name = data.catalogName || data.catalog_name || '服务'
      const elder = data.elderName || data.elder_name || ''
      const when = String(data.bookingTime || data.booking_time || '').replace('T', ' ').slice(0, 16)
      const statusMap = { pending: '待确认', confirmed: '已确认', completed: '已完成', cancelled: '已取消' }
      const status = statusMap[data.status] || data.status || ''
      return ['已预约「' + name + '」', elder ? '服务对象：' + elder : '', when ? '时间：' + when : '', status ? '状态：' + status : '']
        .filter(Boolean)
        .join('；')
    }
    if (action === 'notify_family' || data.notified != null) {
      const count = data.recipientCount ?? data.recipient_count
      const msg = data.message || ''
      const head = count != null ? `已向 ${count} 位家属发送站内消息` : '已向家属发送站内消息'
      return msg ? `${head}：${String(msg).slice(0, 80)}` : head
    }
    if (data.missedCount != null || data.missed_count != null || data.schedules) {
      const missed = data.missedCount ?? data.missed_count ?? 0
      const names = (data.schedules || [])
        .slice(0, 3)
        .map((s) => s.drugName || s.drug_name)
        .filter(Boolean)
      return `用药计划：${names.join('、') || '暂无'}；近三日漏服 ${missed} 次`
    }
    if (data.note || data.message) {
      return String(data.note || data.message)
    }
    return '已完成该项操作'
  } catch {
    return raw
  }
}

const visibleSteps = ref([])
let timer = null

function play() {
  clearTimer()
  visibleSteps.value = []
  if (!props.steps?.length) return
  if (!props.animate) {
    visibleSteps.value = [...props.steps]
    return
  }
  let i = 0
  const tick = () => {
    if (i >= props.steps.length) return
    visibleSteps.value = props.steps.slice(0, i + 1)
    i += 1
    if (i < props.steps.length) {
      timer = setTimeout(tick, 420)
    }
  }
  tick()
}

function clearTimer() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

watch(
  () => props.steps,
  () => play(),
  { immediate: true, deep: true }
)

onBeforeUnmount(clearTimer)
</script>

<style scoped>
.agent-steps {
  margin-top: 10px;
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.agent-steps__title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
}
.agent-steps__item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: #fff;
  border-left: 3px solid #94a3b8;
  font-size: 13px;
  line-height: 1.55;
  color: #334155;
}
.agent-steps__item.is-tool {
  border-left-color: var(--care-green, #2f9b6a);
}
.agent-steps__round {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}
.label {
  display: inline-block;
  min-width: 36px;
  margin-right: 6px;
  color: #64748b;
  font-size: 12px;
}
.agent-steps__tool {
  display: inline-block;
  background: #e8f6ef;
  color: #247a53;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
.agent-steps__obs {
  margin-top: 4px;
  color: #475569;
  display: flex;
  gap: 6px;
  align-items: flex-start;
}
.agent-steps__obs-text {
  flex: 1;
  min-width: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}
.step-fade-enter-active {
  transition: all 0.35s ease;
}
.step-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
