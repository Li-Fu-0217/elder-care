/**
 * Axios 封装：自动附加 JWT、统一解析 Result{code,data}、401 跳转登录。
 * 文件下载请设 responseType: 'blob'（见 downloadFile）。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getActivePinia } from 'pinia'
import { getToken, clearAuth } from './auth'
import { useUserStore } from '@/store/user'
import { teardownSession } from '@/utils/session'
import router from '@/router'

const ERROR_DEDUPE_MS = 3000
let lastErrorToast = { text: '', at: 0 }
let handlingUnauthorized = false

/** Vite 代理在后端未启动时返回 500 + text/plain 空体；生产环境常见 502/503 或无 response */
function isBackendUnavailable(error) {
  if (!error.response) {
    return error.code === 'ERR_NETWORK' || error.message === 'Network Error'
  }
  const { status, data, headers } = error.response
  if (status === 502 || status === 503 || status === 504) {
    return true
  }
  if (status === 500) {
    const contentType = String(headers?.['content-type'] || '')
    if (contentType.includes('text/plain')) {
      return true
    }
    const text = typeof data === 'string' ? data : ''
    if (!text.trim()) {
      return true
    }
    if (/econnrefused|proxy/i.test(text)) {
      return true
    }
  }
  return false
}

function resolveErrorMessage(error) {
  if (isBackendUnavailable(error)) {
    return '后端未启动'
  }
  const backendMsg = error.response?.data?.message
  if (backendMsg) {
    return backendMsg
  }
  const msg = String(error.message || '')
  if (/timeout/i.test(msg)) {
    return '请求超时，请稍后重试'
  }
  if (/Network Error/i.test(msg)) {
    return '网络异常'
  }
  return '网络错误'
}

/** 相同文案在短时间内只弹一次，避免并发请求刷屏 */
function showError(message) {
  const text = String(message || '请求失败').trim()
  const now = Date.now()
  if (text === lastErrorToast.text && now - lastErrorToast.at < ERROR_DEDUPE_MS) {
    return
  }
  lastErrorToast = { text, at: now }
  ElMessage.error({ message: text, grouping: true })
}

function handleUnauthorized() {
  if (handlingUnauthorized) return
  handlingUnauthorized = true
  const pinia = getActivePinia()
  if (pinia) {
    useUserStore(pinia).logout()
    teardownSession()
  } else {
    clearAuth()
  }
  router.push('/login').finally(() => {
    setTimeout(() => {
      handlingUnauthorized = false
    }, 500)
  })
}

const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

/** 查询参数统一转 snake_case，与 FastAPI 入参一致（如 elderId → elder_id） */
function toSnakeCaseKey(key) {
  return String(key).replace(/[A-Z]/g, (ch) => `_${ch.toLowerCase()}`)
}

function snakeCaseParams(params) {
  if (!params || typeof params !== 'object' || Array.isArray(params)) {
    return params
  }
  const out = {}
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue
    out[toSnakeCaseKey(key)] = value
  }
  return out
}

// 请求拦截：所有 /api 请求携带 Bearer Token
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (config.params) {
    config.params = snakeCaseParams(config.params)
  }
  return config
})

request.interceptors.response.use(
  response => {
    // 二进制下载：若后端返回 JSON 错误体则解析提示
    if (response.config.responseType === 'blob') {
      const blob = response.data
      if (blob.type && blob.type.includes('application/json')) {
        return blob.text().then(text => {
          try {
            const json = JSON.parse(text)
            showError(json.message || '请求失败')
          } catch {
            showError('请求失败')
          }
          return Promise.reject(new Error('请求失败'))
        })
      }
      return blob
    }
    const res = response.data
    if (res.code !== 200) {
      showError(res.message || '请求失败')
      if (res.code === 401) {
        handleUnauthorized()
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data
  },
  error => {
    const status = error.response?.status
    const message = resolveErrorMessage(error)
    if (status === 401) {
      handleUnauthorized()
    }
    showError(message)
    return Promise.reject(error)
  }
)

export default request
