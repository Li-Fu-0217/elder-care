import request from '@/utils/request'

export function agentChat(data) {
  return request.post('/agent/chat', data)
}

export function getAgentSessions() {
  return request.get('/agent/sessions')
}

export function getAgentMessages(sessionId) {
  return request.get(`/agent/sessions/${sessionId}/messages`)
}
