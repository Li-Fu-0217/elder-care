/**
 * 各 Pinia store 的 localStorage 持久化配置（由 piniaPersist 插件读取）。
 */
import { useUserStore } from '@/store/user'

const STORAGE_PREFIX_TAGS = 'app-tags-view'

/** @type {import('./piniaPersist').PersistOptions} */
export const userPersist = {
  key: 'pinia-user',
  paths: ['token', 'userInfo'],
  clearWhen: (state) => !state.token,
  migrate() {
    if (localStorage.getItem('pinia-user')) {
      return null
    }
    const token = localStorage.getItem('system_token')
    const userRaw = localStorage.getItem('system_user')
    if (!token && !userRaw) {
      return null
    }
    let userInfo = null
    if (userRaw) {
      try {
        userInfo = JSON.parse(userRaw)
      } catch {
        userInfo = null
      }
    }
    return { token: token || '', userInfo }
  }
}

/** @type {import('./piniaPersist').PersistOptions} */
export const tagsViewPersist = {
  auto: false,
  paths: ['visitedViews'],
  getKey(store) {
    const user = useUserStore().userInfo
    if (!user?.id) {
      return null
    }
    return `${STORAGE_PREFIX_TAGS}-${user.id}-${store.activeScope}`
  },
  serialize(state) {
    return JSON.stringify(state.visitedViews ?? [])
  },
  deserialize(raw) {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return { visitedViews: parsed }
    }
    return parsed && typeof parsed === 'object' ? parsed : { visitedViews: [] }
  }
}

export const persistRegistry = {
  user: userPersist,
  tagsView: tagsViewPersist
}

export function getTagsStorageKeys(userId) {
  if (!userId) {
    return []
  }
  return [`${STORAGE_PREFIX_TAGS}-${userId}-admin`, `${STORAGE_PREFIX_TAGS}-${userId}-user`]
}
