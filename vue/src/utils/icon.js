import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { Menu as MenuIcon } from '@element-plus/icons-vue'

/** Element Plus 图标名列表（已排序） */
export const iconNames = Object.keys(ElementPlusIconsVue).sort()

export function resolveIcon(name) {
  if (!name) return MenuIcon
  return ElementPlusIconsVue[name] || MenuIcon
}
