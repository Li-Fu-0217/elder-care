/**
 * 按钮级权限：按角色控制显示，无需单独权限表。
 * 用法：v-auth="'ADMIN'" 或 v-auth="['ADMIN','USER']"
 * 与路由 meta.roles、后端 require_admin 配合使用。
 */
import { useUserStore } from '@/store/user'

function check(el, binding) {
  const value = binding.value
  if (!value) {
    return
  }
  const codes = Array.isArray(value) ? value : [value]
  const store = useUserStore()
  if (!store.hasAnyRole(...codes)) {
    el.style.display = 'none'
  } else {
    el.style.display = ''
  }
}

export const vAuth = {
  mounted(el, binding) {
    check(el, binding)
  },
  updated(el, binding) {
    check(el, binding)
  }
}
