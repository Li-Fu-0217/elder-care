import request from '@/utils/request'

export function getCareDashboard() {
  return request.get('/care/dashboard')
}

export function getAgentToolLogs(params) {
  return request.get('/admin/agent/tool-logs', { params })
}

/** Agent 工具目录（用途与使用规则） */
export function getAgentTools() {
  return request.get('/admin/agent/tools')
}
