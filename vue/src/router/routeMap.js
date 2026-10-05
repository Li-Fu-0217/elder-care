/**
 * path → 页面组件。
 * /admin/*：须在 menu_paths.py 登记，并在菜单管理或 system.sql 中配置。
 * /user/*：前台固定路由，在 dynamicRoutes.js 写死，不入 sys_menu。
 */
export const routeMap = {
  '/admin/dashboard': () => import('@/views/admin/AdminDashboard.vue'),
  '/admin/elders': () => import('@/views/admin/ElderList.vue'),
  '/admin/medications': () => import('@/views/admin/MedicationList.vue'),
  '/admin/bookings': () => import('@/views/admin/BookingList.vue'),
  '/admin/activities': () => import('@/views/admin/ActivityList.vue'),
  '/admin/alerts': () => import('@/views/admin/AlertList.vue'),
  '/admin/knowledge': () => import('@/views/admin/KnowledgeList.vue'),
  '/admin/agent-tools': () => import('@/views/admin/AgentToolList.vue'),
  '/admin/agent-logs': () => import('@/views/admin/AgentLogList.vue'),
  '/admin/users': () => import('@/views/user/UserList.vue'),
  '/admin/logs': () => import('@/views/log/SystemLogList.vue'),
  '/admin/menus': () => import('@/views/menu/MenuList.vue'),
  '/user/home': () => import('@/views/front/Home.vue'),
  '/user/care': () => import('@/views/front/CareDashboard.vue'),
  '/user/medications': () => import('@/views/front/UserMedications.vue'),
  '/user/notifications': () => import('@/views/front/UserNotifications.vue'),
  '/user/bookings': () => import('@/views/front/UserBookings.vue'),
  '/user/activities': () => import('@/views/front/UserActivities.vue'),
  '/user/agent': () => import('@/views/front/AgentChat.vue'),
  '/user/elders': () => import('@/views/front/CareDashboard.vue'),
  '/user/profile': () => import('@/views/profile/Profile.vue')
}

export const routeMapPaths = Object.keys(routeMap)
