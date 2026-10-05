import router from '@/router'

/** 路由是否允许当前角色访问（根据 meta.roles） */
export function canAccessRoute(path, userRole) {
  try {
    const resolved = router.resolve(path)
    const record = [...resolved.matched].reverse().find((r) => r.meta?.roles?.length)
    if (!record) {
      return true
    }
    return record.meta.roles.includes(userRole)
  } catch {
    return false
  }
}
