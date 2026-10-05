import request from '@/utils/request'

export function getAdminStats() {
  return request.get('/admin/stats')
}
