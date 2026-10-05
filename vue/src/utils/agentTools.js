/**
 * Agent 工具中文名（与管理端「Agent 工具」页、办理过程一致）
 */
export const AGENT_TOOL_LABELS = {
  query_health_record: '查询健康档案',
  check_medication_schedule: '查询用药与漏服',
  query_available_service: '查询可预约时段',
  book_service: '提交服务预约',
  notify_family: '通知子女',
  trigger_emergency_alert: '紧急告警',
  query_knowledge_base: '检索知识库'
}

export function agentToolLabel(name) {
  return AGENT_TOOL_LABELS[name] || name || '-'
}

function parseJson(raw) {
  if (raw == null || raw === '') return null
  if (typeof raw === 'object') return raw
  try {
    return JSON.parse(String(raw))
  } catch {
    return null
  }
}

/** 把入参 JSON 转成一句人话 */
export function formatToolArgs(toolName, raw) {
  const data = parseJson(raw)
  if (!data) return raw ? String(raw) : '-'
  const elder = data.elderId ?? data.elder_id
  const parts = []
  if (elder != null) parts.push(`老人ID ${elder}`)
  if (toolName === 'query_available_service') {
    const typeMap = {
      health_check: '体检',
      nursing: '护理',
      housekeeping: '家政'
    }
    const t = data.service_type || data.type || data.serviceType
    if (t) parts.push(`服务：${typeMap[t] || t}`)
    if (data.days != null) parts.push(`未来 ${data.days} 天`)
  }
  if (toolName === 'book_service') {
    if (data.catalogId ?? data.catalog_id) {
      parts.push(`目录ID ${data.catalogId ?? data.catalog_id}`)
    }
    const bt = data.bookingTime || data.booking_time
    if (bt) parts.push(`时间 ${String(bt).replace('T', ' ').slice(0, 16)}`)
  }
  if (toolName === 'notify_family' && data.message) {
    parts.push(`内容：${String(data.message).slice(0, 40)}`)
  }
  if (toolName === 'trigger_emergency_alert') {
    if (data.location) parts.push(`位置：${data.location}`)
    if (data.message) parts.push(String(data.message).slice(0, 40))
  }
  if (toolName === 'query_knowledge_base') {
    const q = data.question || data.q
    if (q) parts.push(`问题：${String(q).slice(0, 40)}`)
  }
  return parts.length ? parts.join('；') : JSON.stringify(data)
}

/** 把工具返回 JSON 转成一句人话 */
export function formatToolResult(toolName, raw) {
  const data = parseJson(raw)
  if (!data) return raw ? String(raw) : '-'
  if (data.ok === true) return '查询成功'
  if (data.missed != null || data.missedCount != null || data.missed_count != null) {
    const n = data.missed ?? data.missedCount ?? data.missed_count
    return `近几日漏服 ${n} 次`
  }
  if (data.hits != null) return `检索到 ${data.hits} 条知识片段`
  if (data.notified != null || data.recipientCount != null || data.recipient_count != null) {
    const n = data.notified ?? data.recipientCount ?? data.recipient_count
    return `已通知家属（${n}）`
  }
  if (data.bookingId != null || data.booking_id != null) {
    const id = data.bookingId ?? data.booking_id
    return id ? `预约已写入（ID ${id}）` : '预约已提交'
  }
  if (data.slots != null) {
    const n = Array.isArray(data.slots) ? data.slots.length : data.slots
    return `找到 ${n} 个可约时段`
  }
  if (data.alertId != null || data.alert_id != null) {
    return `告警已创建（ID ${data.alertId ?? data.alert_id}）`
  }
  if (data.note || data.message) return String(data.note || data.message).slice(0, 60)
  return JSON.stringify(data)
}
