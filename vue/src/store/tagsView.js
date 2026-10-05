/**
 * 多页签 + keep-alive：按用户 ID 与 scope(admin/user) 持久化到 localStorage。
 * affix 路由（控制台/首页）不可关闭。
 */
import { defineStore } from 'pinia'
import { useUserStore } from '@/store/user'
import { canAccessRoute } from '@/utils/permission'
import { readPersisted, writePersisted } from '@/plugins/piniaPersist'
import { getTagsStorageKeys } from '@/plugins/persistRegistry'
import router from '@/router'

const AFFIX_BY_SCOPE = {
  admin: {
    name: 'AdminDashboard',
    path: '/admin/dashboard',
    fullPath: '/admin/dashboard',
    title: '数据概览',
    affix: true
  },
  user: {
    name: 'FrontHome',
    path: '/user/home',
    fullPath: '/user/home',
    title: '首页',
    affix: true
  }
}

function filterByRole(views, userRole) {
  return views.filter((v) => {
    if (v.path.includes('/403')) {
      return false
    }
    return canAccessRoute(v.path, userRole)
  })
}

function ensureAffix(views, scope) {
  const affix = AFFIX_BY_SCOPE[scope]
  const list = [...views]
  if (affix && !list.some((v) => v.path === affix.path)) {
    list.unshift({ ...affix })
  }
  return list
}

function isCacheable(name) {
  const record = router.getRoutes().find((r) => r.name === name)
  return record && !record.meta?.noCache && !record.meta?.noTag
}

function rebuildCache(visitedViews) {
  return visitedViews.map((v) => v.name).filter((name) => name && isCacheable(name))
}

export const useTagsViewStore = defineStore('tagsView', {
  state: () => ({
    visitedViews: [],
    cachedViews: [],
    restored: false,
    activeScope: 'admin'
  }),
  actions: {
    restoreFromStorage(userRole, scope) {
      this.activeScope = scope
      const affix = AFFIX_BY_SCOPE[scope]
      const user = useUserStore().userInfo
      if (!user?.id) {
        this.visitedViews = affix ? [{ ...affix }] : []
        this.cachedViews = rebuildCache(this.visitedViews)
        this.restored = true
        return
      }
      const saved = readPersisted(this)
      let views = saved?.visitedViews?.length ? saved.visitedViews : affix ? [{ ...affix }] : []
      views = ensureAffix(filterByRole(views, userRole || user.role), scope)
      this.visitedViews = views
      this.cachedViews = rebuildCache(views)
      this.restored = true
    },
    addView(route) {
      if (!route.name || route.meta?.noTag) {
        return
      }
      const title = route.meta?.title || String(route.name)
      const exists = this.visitedViews.find((v) => v.path === route.path)
      if (exists) {
        exists.fullPath = route.fullPath
        writePersisted(this)
        return
      }
      this.visitedViews.push({
        name: route.name,
        path: route.path,
        fullPath: route.fullPath,
        title,
        affix: !!route.meta?.affix
      })
      this.addCache(route)
      writePersisted(this)
    },
    addCache(route) {
      const name = route.name
      if (!name || !isCacheable(name) || this.cachedViews.includes(name)) {
        return
      }
      this.cachedViews.push(name)
    },
    delView(view) {
      if (view.affix) {
        return
      }
      const idx = this.visitedViews.findIndex((v) => v.path === view.path)
      if (idx === -1) {
        return
      }
      this.visitedViews.splice(idx, 1)
      this.delCache(view.name)
      writePersisted(this)
    },
    delCache(name) {
      const idx = this.cachedViews.indexOf(name)
      if (idx > -1) {
        this.cachedViews.splice(idx, 1)
      }
    },
    delOthers(active) {
      this.visitedViews = this.visitedViews.filter((v) => v.affix || v.path === active.path)
      this.syncCacheFromVisited()
      writePersisted(this)
    },
    delAll() {
      this.visitedViews = this.visitedViews.filter((v) => v.affix)
      this.syncCacheFromVisited()
      writePersisted(this)
    },
    syncCacheFromVisited() {
      this.cachedViews = rebuildCache(this.visitedViews)
    },
    clear() {
      const userId = useUserStore().userInfo?.id
      for (const key of getTagsStorageKeys(userId)) {
        localStorage.removeItem(key)
      }
      this.visitedViews = []
      this.cachedViews = []
      this.restored = false
    }
  }
})
