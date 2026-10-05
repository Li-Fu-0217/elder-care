/**
 * Pinia 持久化插件：将 store 指定字段同步到 localStorage。
 * 配置见 persistRegistry.js；各 store 通过 store.$id 匹配。
 */

import { persistRegistry } from './persistRegistry'

/**
 * @typedef {Object} PersistOptions
 * @property {string} [key] 固定 storage key
 * @property {(store: import('pinia').Store) => string | null | undefined} [getKey] 动态 key，返回 null 时不读写
 * @property {string[]} [paths] 需要持久化的 state 字段
 * @property {boolean} [auto=true] 是否在 store 创建时自动 hydrate
 * @property {Storage} [storage]
 * @property {() => object | null} [migrate] 从旧 key 迁移，返回 patch 对象
 * @property {(state: object) => string} [serialize]
 * @property {(raw: string) => object} [deserialize]
 * @property {(store: import('pinia').Store, data: object) => object} [beforeRestore] 恢复前加工数据
 * @property {(state: object) => boolean} [clearWhen] 为 true 时删除 storage 项（如登出）
 */

function pickState(state, paths) {
  if (!paths?.length) {
    return { ...state }
  }
  const picked = {}
  for (const path of paths) {
    if (path in state) {
      picked[path] = state[path]
    }
  }
  return picked
}

function resolveKey(store, opt) {
  if (opt.getKey) {
    return opt.getKey(store)
  }
  return opt.key ?? `pinia-${store.$id}`
}

function getStorage(opt) {
  return opt.storage ?? localStorage
}

export function readPersisted(store, opt = persistRegistry[store.$id]) {
  if (!opt) {
    return null
  }
  const storage = getStorage(opt)
  const key = resolveKey(store, opt)
  if (!key) {
    return null
  }
  const raw = storage.getItem(key)
  if (!raw) {
    return null
  }
  try {
    return opt.deserialize ? opt.deserialize(raw) : JSON.parse(raw)
  } catch {
    return null
  }
}

export function writePersisted(store, opt = persistRegistry[store.$id]) {
  if (!opt) {
    return
  }
  const storage = getStorage(opt)
  const key = resolveKey(store, opt)
  if (!key) {
    return
  }
  const payload = pickState(store.$state, opt.paths)
  if (opt.clearWhen?.(store.$state)) {
    storage.removeItem(key)
    return
  }
  const raw = opt.serialize ? opt.serialize(payload) : JSON.stringify(payload)
  storage.setItem(key, raw)
}

export function removePersisted(key, storage = localStorage) {
  storage.removeItem(key)
}

function hydrate(store, opt) {
  const storage = getStorage(opt)
  let data = null

  if (opt.migrate) {
    const migrated = opt.migrate()
    if (migrated) {
      data = migrated
      const key = resolveKey(store, opt)
      if (key) {
        const raw = opt.serialize ? opt.serialize(migrated) : JSON.stringify(migrated)
        storage.setItem(key, raw)
      }
      localStorage.removeItem('system_token')
      localStorage.removeItem('system_user')
    }
  }

  if (!data) {
    data = readPersisted(store, opt)
  }

  if (!data) {
    return
  }

  const patch = opt.beforeRestore ? opt.beforeRestore(store, data) : data
  if (patch) {
    store.$patch(patch)
  }
}

/**
 * @param {import('pinia').Pinia} pinia
 */
export function piniaPersistPlugin({ store }) {
  const opt = persistRegistry[store.$id]
  if (!opt) {
    return
  }

  if (opt.auto !== false) {
    hydrate(store, opt)
  }

  store.$subscribe(
    () => {
      writePersisted(store, opt)
    },
    { detached: true }
  )
}
