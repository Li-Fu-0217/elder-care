/**
 * 头像 URL：后端返回 /uploads/...，开发环境由 vite 代理到 8000。
 * @param {string|null|undefined} avatar
 */
export function resolveAvatarUrl(avatar) {
  if (!avatar) return ''
  if (/^https?:\/\//i.test(avatar)) return avatar
  return avatar
}

/** 无头像时显示的首字母 */
export function avatarFallbackText(user) {
  const name = user?.nickname || user?.username || '?'
  return String(name).charAt(0).toUpperCase()
}
