/**
 * API client for the RAG application
 * RAG 应用的 API 客户端

 * Day 3 Enhancement: Retrieval configuration
 * Day 3 增强： 检索配置

 * Day 4 Enhancement: Streaming support and citations
 * Day 4 增强： 流式支持和引用

 * Day 5 Enhancement: Evaluation API
 * Day 5 增强： 评估 API
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

// Fix: Add request interceptor to attach JWT token from localStorage
// Without this, all authenticated endpoints (e.g., /audit/*) return 401.
// 修复: 添加请求拦截器，从 localStorage 中附加 JWT token
// 没有此拦截器，所有需要认证的端点（如 /audit/*）都会返回 401。
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Fix: Add response interceptor to handle 401 (expired/invalid token)
// Clear stale credentials and force re-login.
// 修复: 添加响应拦截器处理 401（过期/无效 token）
// 清除过期凭据并强制重新登录。
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
      // Only redirect if not already on the login page
      // 仅当不在登录页面时才重定向
      if (window.location.pathname !== '/login') {
        window.location.reload()
      }
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

// Day 5: QA History types
// Day 5： 问答历史类型
export interface QAHistorySource {
  document_id: string
  filename: string
  score: number
  citation_id: number
}

export interface QAHistoryRecord {
  id: string
  question: string
  answer: string
  contexts: string[]
  sources?: QAHistorySource[]
  retrieval_method?: string
  confidence: number
  created_at: string
  conversation_id?: string
}

export interface QAHistoryListResponse {
  records: QAHistoryRecord[]
  total: number
  page: number
  page_size: number
}

export interface QAHistoryExportRequest {
  record_ids?: string[]
  conversation_id?: string
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
    // Fix: Include Authorization header in fetch() calls too (not just axios)
    // The streaming endpoint uses native fetch, which bypasses axios interceptors.
    // 修复: 在 fetch() 调用中也包含 Authorization header（不仅仅在 axios 中）
    // 流式端点使用原生 fetch，绕过了 axios 拦截器。
    const token = localStorage.getItem('auth_token')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers,
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

// ==================== QA History API Functions (Day 5) ====================
// ==================== 问答历史 API 函数（Day 5）====================

/**
 * Get QA history list with pagination
 * 获取问答历史列表（分页）
 *
 * Day 5: QA history for evaluation
 * Day 5： 用于评估的问答历史
 */
export async function getQAHistoryList(
  page: number = 1,
  pageSize: number = 20,
  conversationId?: string
): Promise<QAHistoryListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  })
  if (conversationId) {
    params.append('conversation_id', conversationId)
  }
  const response = await api.get<QAHistoryListResponse>(`/qa-history?${params.toString()}`)
  return response.data
}

/**
 * Get single QA record by ID
 * 根据 ID 获取单条问答记录
 */
export async function getQAHistoryRecord(recordId: string): Promise<QAHistoryRecord> {
  const response = await api.get<QAHistoryRecord>(`/qa-history/${recordId}`)
  return response.data
}

/**
 * Delete QA record
 * 删除问答记录
 */
export async function deleteQAHistoryRecord(recordId: string): Promise<void> {
  await api.delete(`/qa-history/${recordId}`)
}

/**
 * Export QA history records
 * 导出问答历史记录
 */
export async function exportQAHistory(request: QAHistoryExportRequest): Promise<{
  records: QAHistoryRecord[]
  count: number
  export_format: string
}> {
  const response = await api.post('/qa-history/export', request)
  return response.data
}

/**
 * Get QA statistics
 * 获取问答统计
 */
export async function getQAStats(): Promise<{
  total_records: number
  service_status: string
}> {
  const response = await api.get('/qa-history/stats/summary')
  return response.data
}

// ==================== Authentication Types (Day 6) ====================
// ==================== 认证类型（Day 6）====================

export interface UserInfo {
  id: string
  username: string
  email: string
  role: 'admin' | 'user' | 'viewer'
  is_active: boolean
  created_at?: string
  last_login?: string
}

export interface UserLoginRequest {
  username: string
  password: string
}

export interface UserRegisterRequest {
  username: string
  email: string
  password: string
  role?: 'admin' | 'user' | 'viewer'
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: string
  username: string
  role: string
}

// ==================== User Management Types (Day 6) ====================
// ==================== 用户管理类型（Day 6）====================

export interface UserListResponse {
  users: UserInfo[]
  total: number
}

export interface UserRoleUpdateRequest {
  role: 'admin' | 'user' | 'viewer'
}

// ==================== Audit Log Types (Day 6) ====================
// ==================== 审计日志类型（Day 6）====================

export type AuditActionType =
  | 'login'
  | 'logout'
  | 'login_failed'
  | 'user_create'
  | 'user_update'
  | 'user_deactivate'
  | 'user_activate'
  | 'document_upload'
  | 'document_delete'
  | 'document_view'
  | 'document_download'
  | 'chat_query'
  | 'chat_stream'
  | 'permission_grant'
  | 'permission_revoke'
  | 'system_config_change'
  | 'system_error'

export interface AuditLogEntry {
  id: string
  timestamp: string
  action: AuditActionType
  user_id: string
  username: string
  resource_type?: string
  resource_id?: string
  details?: Record<string, unknown>
  ip_address?: string
  user_agent?: string
  status: string // "success", "failed", "error"
  error_message?: string
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

// ==================== Authentication API Functions (Day 6) ====================
// ==================== 认证 API 函数（Day 6）====================

/**
 * Login and get JWT token
 * 登录并获取 JWT token
 *
 * Day 6: New endpoint for user login
 * Day 6： 用户登录的新端点
 */
export async function login(req: UserLoginRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/login', req)
  return response.data
}

/**
 * Register a new user
 * 注册新用户
 *
 * Day 6: New endpoint for user registration
 * Day 6： 用户注册的新端点
 */
export async function register(req: UserRegisterRequest): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/register', req)
  return response.data
}

/**
 * Logout current user
 * 登出当前用户
 *
 * Day 6: New endpoint for user logout
 * Day 6： 用户登出的新端点
 */
export async function logout(): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/auth/logout')
  return response.data
}

/**
 * Get current user information
 * 获取当前用户信息
 *
 * Day 6: New endpoint for user info
 * Day 6： 用户信息的新端点
 */
export async function getCurrentUser(): Promise<UserInfo> {
  const response = await api.get<UserInfo>('/auth/me')
  return response.data
}

// ==================== User Management API Functions (Day 6) ====================
// ==================== 用户管理 API 函数（Day 6）====================

/**
 * Get list of all users (admin only)
 * 获取所有用户列表（仅管理员）
 *
 * Day 6: New endpoint for user list
 * Day 6： 用户列表的新端点
 */
export async function getUsers(): Promise<UserListResponse> {
  const response = await api.get<UserListResponse>('/auth/users')
  return response.data
}

/**
 * Update a user's role (admin only)
 * 更新用户角色（仅管理员）
 *
 * Day 6: New endpoint for role update
 * Day 6： 角色更新的新端点
 */
export async function updateUserRole(
  userId: string,
  req: UserRoleUpdateRequest
): Promise<UserInfo> {
  const response = await api.put<UserInfo>(`/auth/users/${userId}/role`, req)
  return response.data
}

/**
 * Deactivate a user (admin only)
 * 停用用户（仅管理员）
 *
 * Day 6: New endpoint for user deactivation
 * Day 6： 停用用户的新端点
 */
export async function deactivateUser(userId: string): Promise<UserInfo> {
  const response = await api.post<UserInfo>(`/auth/users/${userId}/deactivate`)
  return response.data
}

/**
 * Activate a user (admin only)
 * 激活用户（仅管理员）
 *
 * Day 6: New endpoint for user activation
 * Day 6： 激活用户的新端点
 */
export async function activateUser(userId: string): Promise<UserInfo> {
  const response = await api.post<UserInfo>(`/auth/users/${userId}/activate`)
  return response.data
}

// ==================== Audit Log API Functions (Day 6) ====================
// ==================== 审计日志 API 函数（Day 6）====================

/**
 * Get audit log list with pagination and filters
 * 获取审计日志列表（分页和过滤）
 *
 * Day 6: New endpoint for audit logs
 * Day 6： 审计日志的新端点
 */
export async function getAuditLogs(
  options?: {
    limit?: number
    offset?: number
    user_id?: string
    action?: string
    resource_type?: string
    resource_id?: string
    status?: string
    start_date?: string
    end_date?: string
  }
): Promise<AuditLogListResponse> {
  const params: Record<string, string> = {}
  if (options?.limit) params.limit = options.limit.toString()
  if (options?.offset) params.offset = options.offset.toString()
  if (options?.user_id) params.user_id = options.user_id
  if (options?.action) params.action = options.action
  if (options?.resource_type) params.resource_type = options.resource_type
  if (options?.resource_id) params.resource_id = options.resource_id
  if (options?.status) params.status = options.status
  if (options?.start_date) params.start_date = options.start_date
  if (options?.end_date) params.end_date = options.end_date

  const queryString = new URLSearchParams(params).toString()
  const response = await api.get<AuditLogListResponse>(
    `/audit/logs${queryString ? `?${queryString}` : ''}`
  )
  return response.data
}

/**
 * Get audit summary statistics
 * 获取审计摘要统计
 *
 * Day 6: New endpoint for audit summary
 * Day 6： 审计摘要的新端点
 */
export async function getAuditSummary(
  days: number = 7
): Promise<AuditSummaryResponse> {
  const response = await api.get<AuditSummaryResponse>(
    `/audit/summary?days=${days}`
  )
  return response.data
}

export default api
