const ROLE_LABELS = {
  ADMIN: '管理员',
  USER: '用户'
}

const ROLE_TAG_TYPES = {
  ADMIN: 'danger',
  USER: 'info'
}

const BOOKING_STATUS = {
  pending: { label: '待确认', type: 'warning' },
  confirmed: { label: '已确认', type: 'primary' },
  cancelled: { label: '已取消', type: 'info' },
  done: { label: '已完成', type: 'success' }
}

const REGISTRATION_STATUS = {
  registered: { label: '已报名', type: 'success' },
  cancelled: { label: '已取消', type: 'info' }
}

const ALERT_STATUS = {
  open: { label: '待处理', type: 'danger' },
  handling: { label: '处理中', type: 'warning' },
  closed: { label: '已关闭', type: 'success' }
}

const MEDICATION_STATUS = {
  0: { label: '漏服', type: 'danger' },
  1: { label: '已服', type: 'success' },
  2: { label: '待服', type: 'warning' }
}

const BOOKING_SOURCE = {
  agent: { label: '智能助手', type: 'primary' },
  manual: { label: '手动', type: 'info' }
}

function pickStatusMeta(dict, status) {
  if (status == null || status === '') {
    return { label: '-', type: 'info' }
  }
  return dict[status] || { label: String(status), type: 'info' }
}

/**
 * 格式化日期时间，ISO 转为 yyyy-MM-dd HH:mm:ss
 */
export function formatDateTime(value) {
  if (value == null || value === '') {
    return '-'
  }
  const text = String(value).replace('T', ' ').replace(/\.\d+/, '')
  return text.length > 19 ? text.slice(0, 19) : text
}

export function roleLabel(role, roleOptions) {
  if (roleOptions?.length) {
    const found = roleOptions.find((r) => r.code === role)
    if (found) {
      return found.name
    }
  }
  return ROLE_LABELS[role] || role || '-'
}

export function roleTagType(role) {
  return ROLE_TAG_TYPES[role] || 'info'
}

/** 账号启用/禁用 */
export function statusLabel(status) {
  return status === 1 ? '启用' : '禁用'
}

export function accountStatusTagType(status) {
  return status === 1 ? 'success' : 'info'
}

export function bookingStatusLabel(status) {
  return pickStatusMeta(BOOKING_STATUS, status).label
}

export function bookingStatusTagType(status) {
  return pickStatusMeta(BOOKING_STATUS, status).type
}

export function registrationStatusLabel(status) {
  return pickStatusMeta(REGISTRATION_STATUS, status).label
}

export function registrationStatusTagType(status) {
  return pickStatusMeta(REGISTRATION_STATUS, status).type
}

export function alertStatusLabel(status) {
  return pickStatusMeta(ALERT_STATUS, status).label
}

export function alertStatusTagType(status) {
  return pickStatusMeta(ALERT_STATUS, status).type
}

export function medicationStatusLabel(status) {
  return pickStatusMeta(MEDICATION_STATUS, status).label
}

export function medicationStatusTagType(status) {
  return pickStatusMeta(MEDICATION_STATUS, status).type
}

export function bookingSourceLabel(source) {
  return pickStatusMeta(BOOKING_SOURCE, source).label
}

export function bookingSourceTagType(source) {
  return pickStatusMeta(BOOKING_SOURCE, source).type
}
