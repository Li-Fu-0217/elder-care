import request from '@/utils/request'

export function getActivities() {
  return request.get('/activities')
}

export function getAdminActivities(params) {
  return request.get('/admin/activities', { params })
}

export function createActivity(data) {
  return request.post('/admin/activities', data)
}

export function updateActivity(id, data) {
  return request.put(`/admin/activities/${id}`, data)
}

export function deleteActivity(id) {
  return request.delete(`/admin/activities/${id}`)
}

export function registerActivity(id, data) {
  return request.post(`/activities/${id}/register`, data)
}

export function getMyRegistrations() {
  return request.get('/activities/my-registrations')
}

export function getAdminRegistrations(params) {
  return request.get('/admin/activities/registrations', { params })
}

export function createEmergencyAlert(data) {
  return request.post('/alerts/emergency', data)
}

export function getAlerts(params) {
  return request.get('/alerts', { params })
}

export function getAdminAlerts(params) {
  return request.get('/admin/alerts', { params })
}

export function updateAlert(id, data) {
  return request.put(`/admin/alerts/${id}`, data)
}
