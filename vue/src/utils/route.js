/** 按角色返回登录后的默认首页（与 sys_menu 首屏路径一致） */
export function getRoleHomePath(role) {
  return role === 'ADMIN' ? '/admin/dashboard' : '/user/home'
}

/** 根据当前路径判断所属端：/admin 或 /user，供个人中心内链使用 */
export function getScopeBasePath(path) {
  if (path.startsWith('/admin')) {
    return '/admin'
  }
  if (path.startsWith('/user')) {
    return '/user'
  }
  return ''
}
