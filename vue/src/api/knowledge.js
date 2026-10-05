import request from '@/utils/request'

export function getKnowledgeDocuments(params) {
  return request.get('/admin/knowledge/documents', { params })
}

export function getKnowledgeChunks(documentId) {
  return request.get(`/admin/knowledge/documents/${documentId}/chunks`)
}

export function uploadKnowledgeDocument(formData) {
  return request.post('/admin/knowledge/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteKnowledgeDocument(id) {
  return request.delete(`/admin/knowledge/documents/${id}`)
}

export function queryKnowledge(data) {
  return request.post('/knowledge/query', data)
}
