/**
 * 个人中心 API：资料、密码、头像绑定。
 */
import request from '@/utils/request'
import { uploadFile } from '@/api/file'

export function updateProfile(data) {
  return request.put('/profile', data)
}

export function changePassword(data) {
  return request.put('/profile/password', data)
}

/**
 * 上传并绑定头像：先通用上传 category=avatar，再写入用户表 avatar 字段
 */
export async function uploadAvatar(file) {
  const fileVo = await uploadFile(file, 'avatar')
  return request.put('/profile/avatar', { path: fileVo.path })
}

/** 仅绑定已有上传路径（path 须为当前用户的 /uploads/avatar/{userId}_*） */
export function bindAvatar(path) {
  return request.put('/profile/avatar', { path })
}
