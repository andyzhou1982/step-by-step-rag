/**
 * API client for the RAG application
 * RAG 应用的 API 客户端

 * Day 3 Enhancement: Retrieval configuration
 * Day 3 增强： 检索配置

 * Day 4 Enhancement: Streaming support and citations
 * Day 4 增强： 流式支持和引用

 * Day 5 Enhancement: Evaluation API
 * Day 5 增强： 评估 API

 * Day 6 Enhancement: Authentication, Permissions, Audit API
 * Day 6 增强： 认证、权限、审计 API
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

// Add auth token to requests if available
// 如果可用，将认证 token 添加到请求中
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
// 处理 401 响应
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

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

// Day 5: Evaluation types
// Day 5： 评估类型
export interface EvaluationMetrics {
  faithfulness: number
  answer_relevance: number
  context_precision: number
  context_recall: number
  overall_score: number
}

export interface RetrievalMetrics {
  recall_at_k: number
  precision_at_k: number
  mrr: number
  ndcg_at_k: number
}

export interface EvaluationRequest {
  question: string
  answer: string
  contexts: string[]
  ground_truth?: string
}

export interface EvaluationResponse {
  rag_metrics: EvaluationMetrics
  retrieval_metrics?: RetrievalMetrics
  evaluation_time_ms: number
  timestamp: string
}

export interface BatchEvaluationRequest {
  questions: string[]
  answers: string[]
  contexts_list: string[][]
  ground_truths?: string[]
}

export interface BatchEvaluationResponse {
  results: EvaluationResponse[]
  average_metrics: EvaluationMetrics
  total_evaluations: number
  total_time_ms: number
}

export interface MetricExplanations {
  rag_metrics: Record<string, string>
  retrieval_metrics: Record<string, string>
}

// Day 6: Authentication types
// Day 6： 认证类型
export interface UserRegisterRequest {
  username: string
  email: string
  password: string
  role?: string
}

export interface UserLoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: string
  username: string
  role: string
}

export interface UserInfo {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  created_at?: string
  last_login?: string
}

export interface UserListResponse {
  users: UserInfo[]
  total: number
}

// Day 6: Permission types
// Day 6： 权限类型
export interface PermissionGrantRequest {
  document_id: string
  user_id: string
  permission: string  // "read", "write", "admin"
}

export interface PermissionInfo {
  document_id: string
  user_id: string
  permission: string
  granted_by: string
  granted_at: string
}

// Day 6: Audit types
// Day 6： 审计类型
export interface AuditLogEntry {
  id: string
  timestamp: string
  action: string
  user_id: string
  username: string
  resource_type: string
  resource_id?: string
  details: Record<string, unknown>
  status: string
}

export interface AuditLogListResponse {
  logs: AuditLogEntry[]
  total: number
  limit: number
  offset: number
}

export interface AuditSummaryResponse {
  period_days: number
  total_actions: number
  unique_users: number
  action_counts: Record<string, number>
  resource_counts: Record<string, number>
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

// ==================== Evaluation API Functions (Day 5) ====================
// ==================== 评估 API 函数（Day 5）====================

/**
 * Evaluate RAG quality
 * 评估 RAG 质量
 *
 * Day 5: RAGAS evaluation endpoint
 * Day 5： RAGAS 评估端点
 */
export async function evaluateRag(request: EvaluationRequest): Promise<EvaluationResponse> {
  const response = await api.post<EvaluationResponse>('/evaluation/rag', request)
  return response.data
}

/**
 * Get metric explanations
 * 获取指标说明
 *
 * Day 5: Documentation endpoint
 * Day 5： 文档端点
 */
export async function getMetricExplanations(): Promise<MetricExplanations> {
  const response = await api.get<MetricExplanations>('/evaluation/metrics/explanations')
  return response.data
}

/**
 * Batch evaluate multiple queries
 * 批量评估多个查询
 *
 * Day 5: Batch evaluation endpoint
 * Day 5： 批量评估端点
 */
export async function batchEvaluate(request: BatchEvaluationRequest): Promise<BatchEvaluationResponse> {
  const response = await api.post<BatchEvaluationResponse>('/evaluation/batch', request)
  return response.data
}

/**
 * Check evaluation service health
 * 检查评估服务健康状态
 *
 * Day 5: Evaluation health check
 * Day 5： 评估健康检查
 */
export async function evaluationHealth(): Promise<{
  evaluation_enabled: boolean
  metrics_enabled: boolean
  tracing_enabled: boolean
}> {
  const response = await api.get('/evaluation/health')
  return response.data
}

// ==================== Authentication API Functions (Day 6) ====================
// ==================== 认证 API 函数（Day 6）====================

/**
 * Register a new user
 * 注册新用户
 *
 * Day 6: User registration
 * Day 6： 用户注册
 */
export async function register(request: UserRegisterRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/register', request)
  return response.data
}

/**
 * Login and get JWT token
 * 登录并获取 JWT token
 *
 * Day 6: User login
 * Day 6： 用户登录
 */
export async function login(request: UserLoginRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/login', request)
  return response.data
}

/**
 * Logout current user
 * 登出当前用户
 *
 * Day 6: User logout
 * Day 6： 用户登出
 */
export async function logout(): Promise<void> {
  await api.post('/auth/logout')
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_info')
}

/**
 * Get current user information
 * 获取当前用户信息
 *
 * Day 6: Get user info
 * Day 6： 获取用户信息
 */
export async function getCurrentUser(): Promise<UserInfo> {
  const response = await api.get<UserInfo>('/auth/me')
  return response.data
}

/**
 * Get all users (admin only)
 * 获取所有用户（仅管理员）
 *
 * Day 6: User list
 * Day 6： 用户列表
 */
export async function getUsers(): Promise<UserListResponse> {
  const response = await api.get<UserListResponse>('/auth/users')
  return response.data
}

/**
 * Update user role (admin only)
 * 更新用户角色（仅管理员）
 *
 * Day 6: Role update
 * Day 6： 角色更新
 */
export async function updateUserRole(userId: string, role: string): Promise<UserInfo> {
  const response = await api.put<UserInfo>(`/auth/users/${userId}/role`, { role })
  return response.data
}

/**
 * Deactivate a user (admin only)
 * 停用用户（仅管理员）
 *
 * Day 6: User deactivation
 * Day 6： 停用用户
 */
export async function deactivateUser(userId: string): Promise<UserInfo> {
  const response = await api.post<UserInfo>(`/auth/users/${userId}/deactivate`)
  return response.data
}

// ==================== Permission API Functions (Day 6) ====================
// ==================== 权限 API 函数（Day 6）====================

/**
 * Grant permission to a user for a document
 * 授予用户对文档的权限
 *
 * Day 6: Permission grant
 * Day 6： 权限授予
 */
export async function grantPermission(request: PermissionGrantRequest): Promise<PermissionInfo> {
  const response = await api.post<PermissionInfo>('/permissions/grant', request)
  return response.data
}

/**
 * Revoke permission from a user for a document
 * 撤销用户对文档的权限
 *
 * Day 6: Permission revoke
 * Day 6： 权限撤销
 */
export async function revokePermission(documentId: string, userId: string): Promise<void> {
  await api.delete(`/permissions/revoke/${documentId}/${userId}`)
}

/**
 * Get permissions for a document
 * 获取文档权限
 *
 * Day 6: Document permissions
 * Day 6： 文档权限
 */
export async function getDocumentPermissions(documentId: string): Promise<PermissionInfo[]> {
  const response = await api.get<{ permissions: PermissionInfo[] }>(`/permissions/document/${documentId}`)
  return response.data.permissions
}

/**
 * Check if user has permission for a document
 * 检查用户对文档是否有权限
 *
 * Day 6: Permission check
 * Day 6： 权限检查
 */
export async function checkPermission(
  documentId: string,
  permission: string
): Promise<{ has_permission: boolean }> {
  const response = await api.get(`/permissions/check/${documentId}`, {
    params: { required_permission: permission }
  })
  return response.data
}

// ==================== Audit API Functions (Day 6) ====================
// ==================== 审计 API 函数（Day 6）====================

/**
 * Get audit logs (admin only)
 * 获取审计日志（仅管理员）
 *
 * Day 6: Audit logs query
 * Day 6： 审计日志查询
 */
export async function getAuditLogs(params?: {
  user_id?: string
  action?: string
  resource_type?: string
  status?: string
  limit?: number
  offset?: number
}): Promise<AuditLogListResponse> {
  const response = await api.get<AuditLogListResponse>('/audit/logs', { params })
  return response.data
}

/**
 * Get system activity summary (admin only)
 * 获取系统活动摘要（仅管理员）
 *
 * Day 6: Activity summary
 * Day 6： 活动摘要
 */
export async function getAuditSummary(days: number = 7): Promise<AuditSummaryResponse> {
  const response = await api.get<AuditSummaryResponse>('/audit/summary', {
    params: { days }
  })
  return response.data
}

/**
 * Get current user's activity
 * 获取当前用户的活动
 *
 * Day 6: User activity
 * Day 6： 用户活动
 */
export async function getMyActivity(days: number = 7): Promise<Record<string, unknown>> {
  const response = await api.get('/audit/my-activity', {
    params: { days }
  })
  return response.data
}

/**
 * Export audit logs (admin only)
 * 导出审计日志（仅管理员）
 *
 * Day 6: Audit export
 * Day 6： 审计导出
 */
export async function exportAuditLogs(format: string = 'json'): Promise<{ data: string }> {
  const response = await api.get('/audit/export', {
    params: { format }
  })
  return response.data
}

export default api
