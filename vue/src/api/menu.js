import request from '@/utils/request'

/** GET /api/menus — 当前用户侧栏菜单 */
export function getMyMenus() {
  return request.get('/menus')
}

/** GET /api/menus/manage — 管理员菜单配置列表 */
export function getMenuManageList(params) {
  return request.get('/menus/manage', { params })
}

/** POST /api/menus */
export function createMenu(data) {
  return request.post('/menus', data)
}

/** PUT /api/menus/:id */
export function updateMenu(id, data) {
  return request.put(`/menus/${id}`, data)
}

/** DELETE /api/menus/:id */
export function deleteMenu(id) {
  return request.delete(`/menus/${id}`)
}

/** DELETE /api/menus/batch */
export function deleteMenus(ids) {
  return request.delete('/menus/batch', { data: ids })
}
