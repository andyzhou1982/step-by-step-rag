/**
 * API client for the RAG application
 * RAG 应用的 API 客户端

 * Day 3 Enhancement: Retrieval configuration
 * Day 3 增强： 检索配置

 * Day 4 Enhancement: Streaming support and citations
 * Day 4 增强： 流式支持和引用
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
  file_type?: string        // Day 3: Added file type
                            // Day 3： 添加了文件类型
  source?: string            // Day 3: Retrieval method
                            // Day 3： 检索方法
  citation_id?: number       // Day 4: Citation ID for reference
                            // Day 4： 引用 ID
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
  stream?: boolean             // Day 4: Enable streaming response
                                // Day 4： 启用流式响应
  max_context_tokens?: number  // Day 4: Max context tokens
                                // Day 4： 最大上下文 token 数
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
  confidence?: number           // Day 4: Confidence score (0-1)
                                 // Day 4： 置信度评分（0-1）
  is_context_based?: boolean    // Day 4: Whether answer is based on context
                                 // Day 4： 答案是否基于上下文
  context_tokens?: number       // Day 4: Number of context tokens used
                                 // Day 4： 使用的上下文 token 数
}

export interface HealthResponse {
  status: string
  database: string
  version: string
  day?: number                  // Day 3: API version day
                                 // Day 3： API 版本天数
  bm25_indexed?: boolean        // Day 3: BM25 index status
                                 // Day 3： BM25 索引状态
  streaming_enabled?: boolean   // Day 4: Streaming support
                                 // Day 4： 流式支持
}

// Day 4: Conversation types
// Day 4： 对话类型
export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceReference[]
}

export interface ConversationHistory {
  conversation_id: string
  messages: ConversationMessage[]
  message_count: number
  created_at: string
  last_updated: string
}

export interface ConversationSummary {
  conversation_id: string
  preview: string
  message_count: number
  created_at: string
  last_updated: string
}

// Day 4: Streaming types
// Day 4： 流式类型
export interface StreamChunk {
  type: 'content' | 'sources' | 'done' | 'error'
  content?: string
  sources?: SourceReference[]
  conversation_id?: string
  confidence?: number
  error?: string
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
 * Ask a question (non-streaming)
 * 提问（非流式）
 */
export async function askQuestion(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/ask', request)
  return response.data
}

/**
 * Ask a question with streaming response
 * 提问并获取流式响应
 *
 * Day 4: New function for SSE streaming
 * Day 4： SSE 流式传输的新函数
 */
export async function askQuestionStream(
  request: ChatRequest,
  onChunk: (chunk: StreamChunk) => void,
  onError?: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Process complete SSE messages
      // 处理完整的 SSE 消息
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onChunk(data as StreamChunk)
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    }
  } catch (error) {
    onError?.(error instanceof Error ? error.message : 'Unknown error')
  }
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
 * Get list of conversations
 * 获取对话列表
 *
 * Day 4: New endpoint for conversation management
 * Day 4： 对话管理的新端点
 */
export async function getConversations(): Promise<ConversationSummary[]> {
  const response = await api.get<ConversationSummary[]>('/chat/conversations')
  return response.data
}

/**
 * Get conversation history
 * 获取对话历史
 *
 * Day 4: New endpoint for conversation retrieval
 * Day 4： 对话检索的新端点
 */
export async function getConversation(conversationId: string): Promise<ConversationHistory> {
  const response = await api.get<ConversationHistory>(`/chat/conversations/${conversationId}`)
  return response.data
}

/**
 * Clear conversation
 * 清除对话
 */
export async function clearConversation(conversationId: string): Promise<void> {
  await api.delete(`/chat/${conversationId}`)
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
