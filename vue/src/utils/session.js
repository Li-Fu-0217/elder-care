import router from '@/router'
import { resetDynamicRoutes } from '@/router/dynamicRoutes'

/** 退出登录时移除动态路由，避免下次登录路由重复 */
export function teardownSession() {
  resetDynamicRoutes(router)
}
