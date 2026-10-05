import request from '@/utils/request'

export function getMedicationSchedules(params) {
  return request.get('/medications/schedules', { params })
}

export function createMedicationSchedule(data) {
  return request.post('/admin/medications/schedules', data)
}

export function updateMedicationSchedule(id, data) {
  return request.put(`/admin/medications/schedules/${id}`, data)
}

export function deleteMedicationSchedule(id) {
  return request.delete(`/admin/medications/schedules/${id}`)
}

export function getMedicationLogs(params) {
  return request.get('/medications/logs', { params })
}

export function markMedicationTaken(id) {
  return request.post(`/medications/logs/${id}/taken`)
}
