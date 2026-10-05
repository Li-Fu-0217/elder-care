/**
 * 登录态：Token + 用户信息，由 piniaPersist 同步至 localStorage（key: pinia-user）。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clearAuth } from '@/utils/auth'
import { login as loginApi, getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref('')
  const userInfo = ref(null)

  const role = computed(() => userInfo.value?.role || '')
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'ADMIN')

  function hasRole(code) {
    return role.value === code
  }

  function hasAnyRole(...codes) {
    return codes.includes(role.value)
  }

  async function login(form) {
    const data = await loginApi(form)
    token.value = data.token
    userInfo.value = data.user
    return data
  }

  async function fetchUser() {
    const data = await getCurrentUser()
    userInfo.value = data
    return data
  }

  function setUserInfo(data) {
    userInfo.value = data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    clearAuth()
  }

  return {
    token,
    userInfo,
    role,
    isLoggedIn,
    isAdmin,
    hasRole,
    hasAnyRole,
    login,
    fetchUser,
    setUserInfo,
    logout
  }
})
