/**
 * API client for communicating with the backend
 * 与后端通信的 API 客户端
 */

import axios from 'axios'

// API base URL
// API 基础 URL
const API_BASE_URL = '/api'

// Create axios instance
// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== Types ====================
// ==================== 类型定义 ====================

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  chunk_count: number
  created_at: string
}

export interface DocumentInfo {
  id: string
  filename: string
  chunk_count: number
  created_at: string
}

export interface DocumentListResponse {
  documents: DocumentInfo[]
  total: number
}

export interface SourceReference {
  document_id: string
  filename: string
  content: string
  score: number
}

export interface ChatRequest {
  question: string
  conversation_id?: string
}

export interface ChatResponse {
  answer: string
  sources: SourceReference[]
  conversation_id: string
}

export interface HealthResponse {
  status: string
  database: string
  version: string
}

// ==================== API Functions ====================
// ==================== API 函数 ====================

/**
 * Upload a document
 * 上传文档
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post<DocumentUploadResponse>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * Get list of all documents
 * 获取所有文档列表
 */
export async function getDocuments(): Promise<DocumentListResponse> {
  const response = await api.get<DocumentListResponse>('/documents/list')
  return response.data
}

/**
 * Delete a document
 * 删除文档
 */
export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/documents/${documentId}`)
}

/**
 * Ask a question
 * 提问
 */
export async function askQuestion(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/ask', request)
  return response.data
}

/**
 * Health check
 * 健康检查
 */
export async function healthCheck(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

export default api
