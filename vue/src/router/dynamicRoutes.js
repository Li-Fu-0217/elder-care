/**
 * 后台：根据 /api/menus 动态注册 /admin 子路由。
 * 前台：/user 路由写死（首页、个人中心等），不读菜单表。
 */
import { routeMap } from './routeMap'

const ADMIN_LAYOUT = 'AdminLayout'
const USER_LAYOUT = 'UserLayout'

let dynamicReady = false

const adminHiddenChildren = [
  {
    path: 'profile',
    name: 'AdminProfile',
    component: () => import('@/views/profile/Profile.vue'),
    meta: { title: '个人信息', roles: ['ADMIN'] }
  },
  {
    path: 'profile/password',
    name: 'AdminChangePassword',
    component: () => import('@/views/profile/ChangePassword.vue'),
    meta: { title: '修改密码', roles: ['ADMIN'] }
  },
  {
    path: '403',
    name: 'AdminForbidden',
    component: () => import('@/views/error/Forbidden.vue'),
    meta: { title: '无权限', noCache: true, noTag: true, roles: ['ADMIN'] }
  }
]

const userFixedChildren = [
  {
    path: 'home',
    name: 'user_home',
    component: routeMap['/user/home'],
    meta: { title: '首页', affix: true, roles: ['USER'] }
  },
  {
    path: 'care',
    name: 'user_care',
    component: routeMap['/user/care'],
    meta: { title: '关怀看板', roles: ['USER'] }
  },
  {
    path: 'medications',
    name: 'user_medications',
    component: routeMap['/user/medications'],
    meta: { title: '服药打卡', roles: ['USER'] }
  },
  {
    path: 'notifications',
    name: 'user_notifications',
    component: routeMap['/user/notifications'],
    meta: { title: '消息中心', roles: ['USER'] }
  },
  {
    path: 'bookings',
    name: 'user_bookings',
    component: routeMap['/user/bookings'],
    meta: { title: '服务预约', roles: ['USER'] }
  },
  {
    path: 'activities',
    name: 'user_activities',
    component: routeMap['/user/activities'],
    meta: { title: '活动天地', roles: ['USER'] }
  },
  {
    path: 'agent',
    name: 'user_agent',
    component: routeMap['/user/agent'],
    meta: { title: '智能助手', roles: ['USER'] }
  },
  {
    path: 'elders/:id',
    name: 'user_elder_detail',
    component: () => import('@/views/front/ElderDetail.vue'),
    meta: { title: '老人档案', roles: ['USER'] }
  },
  {
    path: 'profile',
    name: 'user_profile',
    component: routeMap['/user/profile'],
    meta: { title: '个人中心', roles: ['USER'] }
  },
  {
    path: 'profile/password',
    name: 'FrontChangePassword',
    component: () => import('@/views/profile/ChangePassword.vue'),
    meta: { title: '修改密码', roles: ['USER'] }
  },
  {
    path: '403',
    name: 'FrontForbidden',
    component: () => import('@/views/error/Forbidden.vue'),
    meta: { title: '无权限', noCache: true, noTag: true, roles: ['USER'] }
  }
]

function pathToName(path) {
  return path
    .replace(/^\//, '')
    .replace(/\//g, '_')
    .replace(/-/g, '_')
}

function menuToRoute(menu) {
  const loader = routeMap[menu.path]
  if (!loader) {
    console.warn(`[动态路由] 未注册页面: ${menu.path}，请在 routeMap.js 添加`)
    return null
  }
  const match = menu.path.match(/^\/admin\/(.+)$/)
  if (!match) {
    return null
  }
  return {
    path: match[1],
    name: pathToName(menu.path),
    component: loader,
    meta: {
      title: menu.name,
      roles: ['ADMIN'],
      affix: menu.path === '/admin/dashboard',
      menuPath: menu.path
    }
  }
}

function buildAdminChildren(menus) {
  const adminMenus = menus.filter((m) => m.path?.startsWith('/admin/'))
  const fromMenus = adminMenus.map(menuToRoute).filter(Boolean)
  const paths = new Set(fromMenus.map((r) => r.path))
  const merged = [...fromMenus]
  for (const h of adminHiddenChildren) {
    if (!paths.has(h.path)) {
      merged.push(h)
    }
  }
  return merged
}

function resolveAdminRedirect(menus) {
  const adminMenus = menus.filter((m) => m.path?.startsWith('/admin/'))
  const dash = adminMenus.find((m) => m.path === '/admin/dashboard')
  return dash?.path || adminMenus[0]?.path || '/admin/403'
}

export function isDynamicRoutesReady() {
  return dynamicReady
}

export function resetDynamicRoutes(router) {
  if (router.hasRoute(ADMIN_LAYOUT)) {
    router.removeRoute(ADMIN_LAYOUT)
  }
  if (router.hasRoute(USER_LAYOUT)) {
    router.removeRoute(USER_LAYOUT)
  }
  dynamicReady = false
}

/**
 * @param {import('vue-router').Router} router
 * @param {Array} menus 来自 getMyMenus()（仅含后台菜单）
 */
export function setupDynamicRoutes(router, menus) {
  resetDynamicRoutes(router)

  const adminChildren = buildAdminChildren(menus)
  if (adminChildren.length) {
    router.addRoute({
      path: '/admin',
      name: ADMIN_LAYOUT,
      component: () => import('@/layout/AdminLayout.vue'),
      meta: { scope: 'admin' },
      redirect: resolveAdminRedirect(menus),
      children: adminChildren
    })
  }

  router.addRoute({
    path: '/user',
    name: USER_LAYOUT,
    component: () => import('@/layout/FrontLayout.vue'),
    meta: { scope: 'user' },
    redirect: '/user/home',
    children: userFixedChildren
  })

  dynamicReady = true
}
