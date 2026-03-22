/**
 * Chat interface component for Q&A
 * 问答的聊天界面组件
 *
 * Day 3 Enhancement: Added retrieval configuration panel and display
 * Day 3 增强： 添加了检索配置面板和显示
 */

import { useState, useRef, useEffect } from 'react'
import {
  askQuestion,
  getRetrievalConfig,
  SourceReference,
  RetrievalConfig
} from '../api/client'

// Message type definition
// 消息类型定义
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceReference[]
  retrievalMethod?: string    // Day 3: Retrieval method used
                               // Day 3： 使用的检索方法
  queryRewritten?: boolean    // Day 3: Whether query was rewritten
                               // Day 3： 查询是否被重写
  originalQuery?: string      // Day 3: Original query if rewritten
                               // Day 3： 如果重写了，原始查询
}

// Default retrieval config
// 默认检索配置
const DEFAULT_CONFIG: RetrievalConfig = {
  use_hybrid: true,
  use_rewrite: false,
  use_rerank: true,
  top_k: 5,
  vector_weight: 0.6,
  bm25_weight: 0.4,
}

function ChatInterface() {
  // Messages in conversation
  // 对话中的消息
  const [messages, setMessages] = useState<Message[]>([])
  // Current input
  // 当前输入
  const [input, setInput] = useState('')
  // Loading state
  // 加载状态
  const [loading, setLoading] = useState(false)
  // Conversation ID
  // 对话 ID
  const [conversationId, setConversationId] = useState<string | null>(null)
  // Messages container ref for auto-scroll
  // 消息容器引用，用于自动滚动
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Day 3: Retrieval configuration state
  // Day 3： 检索配置状态
  const [config, setConfig] = useState<RetrievalConfig>(DEFAULT_CONFIG)
  const [showConfig, setShowConfig] = useState(false)

  /**
   * Load retrieval config from backend
   * 从后端加载检索配置
   */
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await getRetrievalConfig()
        setConfig(response.config)
      } catch {
        // Use default config if loading fails
        // 如果加载失败，使用默认配置
      }
    }
    loadConfig()
  }, [])

  /**
   * Scroll to bottom of messages
   * 滚动到消息底部
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Auto-scroll when messages change
  // 消息变化时自动滚动
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  /**
   * Handle sending a message
   * 处理发送消息
   */
  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
    }

    // Add user message
    // 添加用户消息
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await askQuestion({
        question: userMessage.content,
        conversation_id: conversationId || undefined,
        retrieval_config: config,  // Day 3: Include retrieval config
                                     // Day 3： 包含检索配置
      })

      // Save conversation ID
      // 保存对话 ID
      setConversationId(response.conversation_id)

      // Add assistant message
      // 添加助手消息
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        retrievalMethod: response.retrieval_method,  // Day 3
        queryRewritten: response.query_rewritten,    // Day 3
        originalQuery: response.original_query || undefined,  // Day 3
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      // Add error message
      // 添加错误消息
      const errorMessageObj: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errorMessage}\n错误: ${errorMessage}`,
      }
      setMessages(prev => [...prev, errorMessageObj])
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle Enter key press
   * 处理回车键按下
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  /**
   * Clear conversation
   * 清除对话
   */
  const handleClear = () => {
    setMessages([])
    setConversationId(null)
  }

  /**
   * Get retrieval method badge color
   * 获取检索方法徽章颜色
   */
  const getMethodBadgeColor = (method?: string) => {
    switch (method) {
      case 'hybrid':
        return 'bg-purple-100 text-purple-800'
      case 'vector':
        return 'bg-blue-100 text-blue-800'
      case 'bm25':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
        {/* Header */}
        {/* 头部 */}
        <div className="p-4 border-b flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">Chat / 问答</h2>
            <p className="text-sm text-gray-500">
              Ask questions about your uploaded documents
              <br />
              就您上传的文档提问
            </p>
          </div>
          <div className="flex space-x-2">
            {/* Day 3: Config toggle button */}
            {/* Day 3： 配置切换按钮 */}
            <button
              onClick={() => setShowConfig(!showConfig)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                showConfig
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              ⚙️ Config / 配置
            </button>
            {messages.length > 0 && (
              <button
                onClick={handleClear}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                🗑️ Clear / 清除
              </button>
            )}
          </div>
        </div>

        {/* Day 3: Retrieval Configuration Panel */}
        {/* Day 3： 检索配置面板 */}
        {showConfig && (
          <div className="p-4 border-b bg-gray-50">
            <h3 className="text-sm font-medium mb-3">
              Retrieval Configuration / 检索配置
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Hybrid Search Toggle */}
              {/* 混合检索开关 */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.use_hybrid ?? true}
                  onChange={(e) => setConfig({ ...config, use_hybrid: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">
                  Hybrid Search
                  <br />
                  <span className="text-xs text-gray-500">混合检索</span>
                </span>
              </label>

              {/* Query Rewrite Toggle */}
              {/* 查询重写开关 */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.use_rewrite ?? false}
                  onChange={(e) => setConfig({ ...config, use_rewrite: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">
                  Query Rewrite
                  <br />
                  <span className="text-xs text-gray-500">查询重写</span>
                </span>
              </label>

              {/* Re-rank Toggle */}
              {/* 重排序开关 */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={config.use_rerank ?? true}
                  onChange={(e) => setConfig({ ...config, use_rerank: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">
                  Re-rank
                  <br />
                  <span className="text-xs text-gray-500">重排序</span>
                </span>
              </label>

              {/* Top K */}
              <div className="flex items-center space-x-2">
                <span className="text-sm">Top K:</span>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={config.top_k ?? 5}
                  onChange={(e) => setConfig({ ...config, top_k: parseInt(e.target.value) || 5 })}
                  className="w-16 border rounded px-2 py-1 text-sm"
                />
              </div>
            </div>

            {/* Weight sliders for hybrid search */}
            {/* 混合检索的权重滑块 */}
            {config.use_hybrid && (
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm">
                    Vector Weight: {config.vector_weight ?? 0.6}
                    <br />
                    <span className="text-xs text-gray-500">向量权重</span>
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={config.vector_weight ?? 0.6}
                    onChange={(e) => setConfig({
                      ...config,
                      vector_weight: parseFloat(e.target.value)
                    })}
                    className="w-full mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm">
                    BM25 Weight: {config.bm25_weight ?? 0.4}
                    <br />
                    <span className="text-xs text-gray-500">BM25 权重</span>
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={config.bm25_weight ?? 0.4}
                    onChange={(e) => setConfig({
                      ...config,
                      bm25_weight: parseFloat(e.target.value)
                    })}
                    className="w-full mt-1"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        {/* 消息 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-4xl mb-4">💬</p>
              <p className="text-lg">Start a conversation / 开始对话</p>
              <p className="text-sm mt-2">
                Upload documents first, then ask questions about them.
                <br />
                先上传文档，然后针对文档提问。
              </p>
              {/* Day 3: Current config info */}
              {/* Day 3： 当前配置信息 */}
              <div className="mt-4 text-xs">
                <p className="font-medium">Current Config / 当前配置:</p>
                <p>
                  {config.use_hybrid ? '🔀 Hybrid' : '📊 Vector'} |
                  {config.use_rewrite ? ' ✍️ Rewrite' : ''} |
                  {config.use_rerank ? ' 🎯 Rerank' : ''} |
                  Top {config.top_k}
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {/* Day 3: Show retrieval info for assistant messages */}
                  {/* Day 3： 显示助手消息的检索信息 */}
                  {message.role === 'assistant' && (
                    <>
                      {/* Retrieval method and query rewrite info */}
                      {/* 检索方法和查询重写信息 */}
                      {message.retrievalMethod && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs ${getMethodBadgeColor(message.retrievalMethod)}`}>
                            {message.retrievalMethod === 'hybrid' && '🔀 Hybrid'}
                            {message.retrievalMethod === 'vector' && '📊 Vector'}
                            {message.retrievalMethod === 'bm25' && '📝 BM25'}
                          </span>
                          {message.queryRewritten && message.originalQuery && (
                            <span className="px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800">
                              ✍️ Rewritten
                            </span>
                          )}
                        </div>
                      )}

                      {/* Original query if rewritten */}
                      {/* 如果重写了，显示原始查询 */}
                      {message.queryRewritten && message.originalQuery && (
                        <div className="mt-2 text-xs text-gray-500 italic">
                          Original / 原始: &quot;{message.originalQuery}&quot;
                        </div>
                      )}
                    </>
                  )}

                  {/* Show sources for assistant messages */}
                  {/* 显示助手消息的来源 */}
                  {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-500 mb-2">
                        📚 Sources / 来源:
                      </p>
                      <div className="space-y-2">
                        {message.sources.map((source, index) => (
                          <div
                            key={index}
                            className="text-xs bg-white p-2 rounded border"
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{source.filename}</span>
                              <div className="flex items-center space-x-2">
                                {/* Day 3: Show file type */}
                                {/* Day 3： 显示文件类型 */}
                                {source.file_type && (
                                  <span className="text-xs text-gray-400">
                                    {source.file_type}
                                  </span>
                                )}
                                <span className="text-gray-400">
                                  Score: {source.score.toFixed(4)}
                                </span>
                              </div>
                            </div>
                            <p className="text-gray-600 mt-1 line-clamp-2">
                              {source.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Loading indicator */}
          {/* 加载指示器 */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-4">
                <p className="text-gray-500">
                  Thinking... / 思考中...
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {/* 输入 */}
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question here... / 在这里输入您的问题..."
              className="flex-1 border rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className={`px-6 rounded-lg font-medium transition-colors ${
                !input.trim() || loading
                  ? 'bg-gray-100 text-gray-400'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              Send
              <br />
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
