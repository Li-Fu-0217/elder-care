/**
 * 登录态 localStorage 读写（与 Pinia user store 共用 pinia-user key）。
 * 路由守卫、Axios 在 Pinia 未就绪时也可读取。
 */
const PINIA_USER_KEY = 'pinia-user'
const LEGACY_TOKEN_KEY = 'system_token'
const LEGACY_USER_KEY = 'system_user'

function readPiniaUserRaw() {
  return localStorage.getItem(PINIA_USER_KEY)
}

function parsePiniaUser() {
  const raw = readPiniaUserRaw()
  if (!raw) {
    return migrateLegacyAuth()
  }
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function migrateLegacyAuth() {
  const token = localStorage.getItem(LEGACY_TOKEN_KEY)
  const userRaw = localStorage.getItem(LEGACY_USER_KEY)
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
  const payload = { token: token || '', userInfo }
  localStorage.setItem(PINIA_USER_KEY, JSON.stringify(payload))
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
  return payload
}

export function getToken() {
  return parsePiniaUser()?.token || ''
}

export function getUser() {
  return parsePiniaUser()?.userInfo ?? null
}

export function clearAuth() {
  localStorage.removeItem(PINIA_USER_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
}
