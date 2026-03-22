/**
 * API client for communicating with the backend
 * 与后端通信的 API 客户端
 *
 * Day 3 Enhancement: Added retrieval configuration types
 * Day 3 增强： 添加了检索配置类型
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
  file_type?: string  // Day 3: Added file type
                        // Day 3： 添加了文件类型
}

// Day 3: Retrieval configuration type
// Day 3： 检索配置类型
export interface RetrievalConfig {
  use_hybrid?: boolean
  use_rewrite?: boolean
  use_rerank?: boolean
  top_k?: number
  vector_weight?: number
  bm25_weight?: number
}

// Day 3: Retrieval config response type
// Day 3： 检索配置响应类型
export interface RetrievalConfigResponse {
  config: RetrievalConfig
  available_strategies: string[]
  features: string[]
}

export interface ChatRequest {
  question: string
  conversation_id?: string
  file_types?: string[]        // Day 2: Added file type filter
                                // Day 2： 添加了文件类型过滤
  retrieval_config?: RetrievalConfig  // Day 3: Added retrieval config
                                        // Day 3： 添加了检索配置
}

export interface ChatResponse {
  answer: string
  sources: SourceReference[]
  conversation_id: string
  retrieval_method?: string     // Day 3: Retrieval method used
                                 // Day 3： 使用的检索方法
  query_rewritten?: boolean     // Day 3: Whether query was rewritten
                                 // Day 3： 查询是否被重写
  original_query?: string | null  // Day 3: Original query if rewritten
                                   // Day 3： 如果重写了，原始查询
}

export interface HealthResponse {
  status: string
  database: string
  version: string
  day?: number                  // Day 3: API version day
                                 // Day 3： API 版本天数
  bm25_indexed?: boolean        // Day 3: BM25 index status
                                 // Day 3： BM25 索引状态
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
 * Get retrieval configuration
 * 获取检索配置
 *
 * Day 3: New endpoint for retrieval settings
 * Day 3： 检索设置的新端点
 */
export async function getRetrievalConfig(): Promise<RetrievalConfigResponse> {
  const response = await api.get<RetrievalConfigResponse>('/chat/retrieval-config')
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
