import request from '@/utils/request'

export function getElderPage(params) {
  return request.get('/elders', { params })
}

export function getElderById(id) {
  return request.get(`/elders/${id}`)
}

export function getElderHealth(id) {
  return request.get(`/elders/${id}/health`)
}

export function createElder(data) {
  return request.post('/elders', data)
}

export function updateElder(id, data) {
  return request.put(`/elders/${id}`, data)
}

export function deleteElder(id) {
  return request.delete(`/elders/${id}`)
}

export function getMyElders() {
  return request.get('/family/my-elders')
}

export function getMyBindings() {
  return request.get('/family/bindings')
}

/** 子女自助绑定：姓名 + 手机号须与档案一致 */
export function selfBindFamily(data) {
  return request.post('/family/bind', data)
}

export function selfUnbindFamily(id) {
  return request.delete(`/family/bindings/${id}`)
}

export function listFamily(params) {
  return request.get('/admin/family', { params })
}

export function bindFamily(data) {
  return request.post('/admin/family', data)
}

export function unbindFamily(id) {
  return request.delete(`/admin/family/${id}`)
}
