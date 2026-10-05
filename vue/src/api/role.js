import request from '@/utils/request'

export function getRoleList() {
  return request.get('/roles')
}
