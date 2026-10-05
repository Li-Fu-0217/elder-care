/**
 * 通用文件 API，对应后端 FileController。
 * 展示图片可直接用返回的 path（/uploads/...）；下载用 downloadFile 带 Token。
 */
import request from '@/utils/request'

/**
 * 上传文件
 * @param {File} file
 * @param {string} category avatar | common
 */
export function uploadFile(file, category = 'common') {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/files/upload', formData, {
    params: { category }
  })
}

/**
 * 下载文件（带 Token，触发浏览器保存）
 */
export async function downloadFile(path, filename) {
  const blob = await request.get('/files/download', {
    params: { path },
    responseType: 'blob'
  })
  const name = filename || path.split('/').pop() || 'download'
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  URL.revokeObjectURL(url)
}

/**
 * 预览地址（inline，需登录；img 展示建议直接用 /uploads 静态路径）
 */
export function getPreviewUrl(path) {
  const encoded = encodeURIComponent(path)
  return `/api/files/preview?path=${encoded}`
}

export function deleteFile(path) {
  return request.delete('/files', { params: { path } })
}
