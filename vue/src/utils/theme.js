const STORAGE_KEY = 'app-theme-color'

export const themeOptions = [
  { id: 'blue', label: '晴蓝', color: '#2563eb' },
  { id: 'green', label: '翠绿', color: '#059669' },
  { id: 'cyan', label: '青碧', color: '#0891b2' },
  { id: 'purple', label: '暮紫', color: '#7c3aed' },
  { id: 'orange', label: '暖橙', color: '#ea580c' },
  { id: 'rose', label: '玫红', color: '#e11d48' }
]

function parseHex(hex) {
  const h = hex.replace('#', '')
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16)
  }
}

function toHex({ r, g, b }) {
  return (
    '#' +
    [r, g, b]
      .map((v) =>
        Math.round(Math.max(0, Math.min(255, v)))
          .toString(16)
          .padStart(2, '0')
      )
      .join('')
  )
}

function mix(hex, target, ratio) {
  const a = parseHex(hex)
  const b = parseHex(target)
  return toHex({
    r: a.r + (b.r - a.r) * ratio,
    g: a.g + (b.g - a.g) * ratio,
    b: a.b + (b.b - a.b) * ratio
  })
}

function buildThemeVars(primary) {
  return {
    '--app-primary': primary,
    '--app-primary-light': mix(primary, '#ffffff', 0.25),
    '--app-primary-dark': mix(primary, '#000000', 0.15),
    '--app-sidebar-active': primary,
    '--el-color-primary': primary,
    '--el-color-primary-light-3': mix(primary, '#ffffff', 0.3),
    '--el-color-primary-light-5': mix(primary, '#ffffff', 0.5),
    '--el-color-primary-light-7': mix(primary, '#ffffff', 0.7),
    '--el-color-primary-light-8': mix(primary, '#ffffff', 0.8),
    '--el-color-primary-light-9': mix(primary, '#ffffff', 0.92),
    '--el-color-primary-dark-2': mix(primary, '#000000', 0.2)
  }
}

export function getStoredThemeId() {
  const saved = localStorage.getItem(STORAGE_KEY)
  return themeOptions.some((t) => t.id === saved) ? saved : 'blue'
}

export function applyTheme(themeId) {
  const option = themeOptions.find((t) => t.id === themeId) || themeOptions[0]
  const vars = buildThemeVars(option.color)
  const root = document.documentElement
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
  root.dataset.theme = option.id
  localStorage.setItem(STORAGE_KEY, option.id)
  return option.id
}

export function initTheme() {
  return applyTheme(getStoredThemeId())
}
