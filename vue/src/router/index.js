/**
 * 路由：公共页静态注册；/admin、/user 子路由由 dynamicRoutes.js 按菜单动态注入。
 */
import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUser } from '@/utils/auth'
import { getRoleHomePath } from '@/utils/route'
import { useUserStore } from '@/store/user'
import { getMyMenus } from '@/api/menu'
import {
  isDynamicRoutesReady,
  resetDynamicRoutes,
  setupDynamicRoutes
} from '@/router/dynamicRoutes'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    redirect: () => {
      const token = getToken()
      if (!token) {
        return '/login'
      }
      return getRoleHomePath(getUser()?.role)
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

async function ensureUser() {
  const userStore = useUserStore()
  if (!userStore.userInfo) {
    await userStore.fetchUser()
  }
  return userStore
}

async function ensureDynamicRoutes() {
  if (isDynamicRoutesReady()) {
    return
  }
  const menus = await getMyMenus()
  setupDynamicRoutes(router, Array.isArray(menus) ? menus : [])
}

router.beforeEach(async (to, from, next) => {
  const token = getToken()

  if (!to.meta.public && !token) {
    next('/login')
    return
  }

  if (to.meta.public) {
    if (token && (to.path === '/login' || to.path === '/register')) {
      const userStore = await ensureUser()
      try {
        await ensureDynamicRoutes()
        const intended = to.redirectedFrom?.fullPath || to.redirectedFrom?.path
        const fallback = getRoleHomePath(userStore.role)
        const target =
          intended &&
          intended !== '/login' &&
          intended !== '/register' &&
          (intended.startsWith('/admin') || intended.startsWith('/user'))
            ? intended
            : fallback
        next({ path: target, replace: true })
      } catch {
        next('/login')
      }
      return
    }
    next()
    return
  }

  let userStore
  try {
    userStore = await ensureUser()
    if (!isDynamicRoutesReady()) {
      await ensureDynamicRoutes()
      next({ ...to, replace: true })
      return
    }
  } catch {
    resetDynamicRoutes(router)
    next('/login')
    return
  }

  if (to.matched.length === 0) {
    next(getRoleHomePath(userStore.role))
    return
  }

  const scope = to.matched.find((r) => r.meta.scope)?.meta.scope
  if (scope === 'admin' && !userStore.isAdmin) {
    next('/user/403')
    return
  }
  if (scope === 'user' && userStore.isAdmin) {
    next('/admin/403')
    return
  }

  const requiredRoles = to.meta.roles
  if (requiredRoles?.length && !userStore.hasAnyRole(...requiredRoles)) {
    next(scope === 'admin' ? '/admin/403' : '/user/403')
    return
  }

  next()
})

export default router
