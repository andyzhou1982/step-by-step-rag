/**
 * Chat interface component for Q&A
 * 问答的聊天界面组件
 *
 * Day 3 Enhancement: Retrieval configuration panel and display
 * Day 3 增强： 检索配置面板和显示
 *
 * Day 4 Enhancement: Streaming support, citations, and confidence scoring
 * Day 4 增强： 流式支持、引用溯源和置信度评分
 */
import { useState, useRef, useEffect } from 'react'
import {
  askQuestion,
  askQuestionStream,
  getRetrievalConfig,
  SourceReference,
  RetrievalConfig,
  StreamChunk,
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
  confidence?: number         // Day 4: Confidence score
                               // Day 4： 置信度评分
  isContextBased?: boolean    // Day 4: Whether based on context
                               // Day 4： 是否基于上下文
  isStreaming?: boolean       // Day 4: Currently streaming
                               // Day 4： 当前正在流式传输
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

  // Day 4: Streaming and citation state
  // Day 4： 流式传输和引用状态
  const [useStreaming, setUseStreaming] = useState(true)
  const [selectedCitation, setSelectedCitation] = useState<SourceReference | null>(null)

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
   * Handle sending a message (non-streaming)
   * 处理发送消息（非流式）
   */
  const handleSendNonStreaming = async (userMessage: Message) => {
    const response = await askQuestion({
      question: userMessage.content,
      conversation_id: conversationId || undefined,
      retrieval_config: config,
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
      retrievalMethod: response.retrieval_method,
      queryRewritten: response.query_rewritten,
      originalQuery: response.original_query || undefined,
      confidence: response.confidence,
      isContextBased: response.is_context_based,
    }
    setMessages(prev => [...prev, assistantMessage])
  }

  /**
   * Handle sending a message (streaming)
   * 处理发送消息（流式）
   *
   * Day 4: New streaming handler
   * Day 4： 新的流式处理程序
   */
  const handleSendStreaming = async (userMessage: Message) => {
    // Create placeholder message for streaming
    // 为流式传输创建占位消息
    const streamingMessageId = (Date.now() + 1).toString()
    const streamingMessage: Message = {
      id: streamingMessageId,
      role: 'assistant',
      content: '',
      sources: [],
      isStreaming: true,
    }
    setMessages(prev => [...prev, streamingMessage])

    let fullContent = ''
    let sources: SourceReference[] = []
    let confidence = 0

    await askQuestionStream(
      {
        question: userMessage.content,
        conversation_id: conversationId || undefined,
        retrieval_config: config,
        stream: true,
      },
      (chunk: StreamChunk) => {
        if (chunk.type === 'content' && chunk.content) {
          // Append content
          // 追加内容
          fullContent += chunk.content
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageId
                ? { ...msg, content: fullContent }
                : msg
            )
          )
        } else if (chunk.type === 'sources' && chunk.sources) {
          // Store sources
          // 存储来源
          sources = chunk.sources
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageId
                ? { ...msg, sources }
                : msg
            )
          )
        } else if (chunk.type === 'done') {
          // Finalize message
          // 完成消息
          if (chunk.conversation_id) {
            setConversationId(chunk.conversation_id)
          }
          confidence = chunk.confidence || 0

          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageId
                ? {
                    ...msg,
                    content: fullContent,
                    sources,
                    confidence,
                    isStreaming: false,
                  }
                : msg
            )
          )
        } else if (chunk.type === 'error') {
          // Handle error
          // 处理错误
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingMessageId
                ? {
                    ...msg,
                    content: `Error: ${chunk.error || 'Unknown error'}\n错误: ${chunk.error || '未知错误'}`,
                    isStreaming: false,
                  }
                : msg
            )
          )
        }
      },
      (error: string) => {
        // Handle connection error
        // 处理连接错误
        setMessages(prev =>
          prev.map(msg =>
            msg.id === streamingMessageId
              ? {
                  ...msg,
                  content: `Connection Error: ${error}\n连接错误: ${error}`,
                  isStreaming: false,
                }
              : msg
          )
        )
      }
    )
  }

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
      // Day 4: Use streaming or non-streaming based on config
      // Day 4： 根据配置使用流式或非流式
      if (useStreaming) {
        await handleSendStreaming(userMessage)
      } else {
        await handleSendNonStreaming(userMessage)
      }
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
    setSelectedCitation(null)
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

  /**
   * Get confidence badge color
   * 获取置信度徽章颜色
   *
   * Day 4: New helper for confidence display
   * Day 4： 置信度显示的新辅助函数
   */
  const getConfidenceBadgeColor = (confidence?: number) => {
    if (confidence === undefined) return 'bg-gray-100 text-gray-800'
    if (confidence >= 0.7) return 'bg-green-100 text-green-800'
    if (confidence >= 0.4) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  /**
   * Handle citation click
   * 处理引用点击
   *
   * Day 4: New handler for citation interaction
   * Day 4： 引用交互的新处理程序
   */
  const handleCitationClick = (source: SourceReference) => {
    setSelectedCitation(source)
  }

  /**
   * Render answer with clickable citations
   * 渲染带可点击引用的答案
   *
   * Day 4: Parse citations and make them interactive
   * Day 4： 解析引用并使其可交互
   */
  const renderAnswerWithCitations = (content: string, sources?: SourceReference[]) => {
    if (!sources || sources.length === 0) {
      return content
    }

    // Replace citation markers with clickable spans
    // 用可点击的 span 替换引用标记
    const citationRegex = /\[(\d+)\]/g
    const parts: React.ReactNode[] = []
    let lastIndex = 0
    let match

    while ((match = citationRegex.exec(content)) !== null) {
      // Add text before the citation
      // 添加引用之前的文本
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index))
      }

      const citationNum = parseInt(match[1])
      const source = sources.find(s => s.citation_id === citationNum)

      if (source) {
        parts.push(
          <button
            key={`citation-${match.index}`}
            onClick={() => handleCitationClick(source)}
            className="inline-flex items-center justify-center w-5 h-5 text-xs bg-blue-500 text-white rounded-full hover:bg-blue-600 cursor-pointer mx-0.5"
            title={`${source.filename}: ${source.content.substring(0, 50)}...`}
          >
            {citationNum}
          </button>
        )
      } else {
        parts.push(match[0])
      }

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    // 添加剩余文本
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex))
    }

    return parts.length > 0 ? parts : content
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
            {/* Day 4: Streaming toggle */}
            {/* Day 4： 流式开关 */}
            <label className="flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-md">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm">Stream / 流式</span>
            </label>
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

        {/* Main content area with citation panel */}
        {/* 带引用面板的主内容区域 */}
        <div className="flex-1 flex overflow-hidden">
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
                {/* Day 4: Current config info */}
                {/* Day 4： 当前配置信息 */}
                <div className="mt-4 text-xs">
                  <p className="font-medium">Current Config / 当前配置:</p>
                  <p>
                    {config.use_hybrid ? '🔀 Hybrid' : '📊 Vector'} |
                    {config.use_rewrite ? ' ✍️ Rewrite' : ''} |
                    {config.use_rerank ? ' 🎯 Rerank' : ''} |
                    {useStreaming ? ' 📡 Stream' : ' 📦 Batch'} |
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
                    {/* Day 4: Render answer with clickable citations */}
                    {/* Day 4： 渲染带可点击引用的答案 */}
                    <div className="whitespace-pre-wrap">
                      {message.role === 'assistant'
                        ? renderAnswerWithCitations(message.content, message.sources)
                        : message.content}
                      {/* Day 4: Streaming indicator */}
                      {/* Day 4： 流式指示器 */}
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
                      )}
                    </div>

                    {/* Day 3: Show retrieval info for assistant messages */}
                    {/* Day 3： 显示助手消息的检索信息 */}
                    {message.role === 'assistant' && !message.isStreaming && (
                      <>
                        {/* Retrieval method, confidence, and query rewrite info */}
                        {/* 检索方法、置信度和查询重写信息 */}
                        <div className="mt-2 flex flex-wrap gap-2">
                          {message.retrievalMethod && (
                            <span className={`px-2 py-0.5 rounded-full text-xs ${getMethodBadgeColor(message.retrievalMethod)}`}>
                              {message.retrievalMethod === 'hybrid' && '🔀 Hybrid'}
                              {message.retrievalMethod === 'vector' && '📊 Vector'}
                              {message.retrievalMethod === 'bm25' && '📝 BM25'}
                            </span>
                          )}
                          {/* Day 4: Confidence badge */}
                          {/* Day 4： 置信度徽章 */}
                          {message.confidence !== undefined && (
                            <span className={`px-2 py-0.5 rounded-full text-xs ${getConfidenceBadgeColor(message.confidence)}`}>
                              📊 {(message.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                          {message.queryRewritten && (
                            <span className="px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800">
                              ✍️ Rewritten
                            </span>
                          )}
                        </div>

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
                    {message.role === 'assistant' && message.sources && message.sources.length > 0 && !message.isStreaming && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-500 mb-2">
                          📚 Sources / 来源 ({message.sources.length})
                        </p>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {message.sources.map((source, index) => (
                            <div
                              key={index}
                              onClick={() => handleCitationClick(source)}
                              className={`text-xs bg-white p-2 rounded border cursor-pointer hover:bg-blue-50 transition-colors ${
                                selectedCitation === source ? 'border-blue-500 bg-blue-50' : ''
                              }`}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium flex items-center">
                                  {/* Day 4: Citation ID */}
                                  {/* Day 4： 引用 ID */}
                                  {source.citation_id && (
                                    <span className="inline-flex items-center justify-center w-4 h-4 text-xs bg-blue-500 text-white rounded-full mr-2">
                                      {source.citation_id}
                                    </span>
                                  )}
                                  {source.filename}
                                </span>
                                <div className="flex items-center space-x-2">
                                  {source.file_type && (
                                    <span className="text-xs text-gray-400">
                                      {source.file_type}
                                    </span>
                                  )}
                                  <span className="text-gray-400">
                                    {(source.score * 100).toFixed(1)}%
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
            {loading && !useStreaming && (
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

          {/* Day 4: Citation detail panel */}
          {/* Day 4： 引用详情面板 */}
          {selectedCitation && (
            <div className="w-64 border-l bg-gray-50 p-4 overflow-y-auto">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-medium">Citation / 引用</h3>
                <button
                  onClick={() => setSelectedCitation(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-500">File / 文件</p>
                  <p className="text-sm font-medium">{selectedCitation.filename}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Type / 类型</p>
                  <p className="text-sm">{selectedCitation.file_type}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Score / 分数</p>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${selectedCitation.score * 100}%` }}
                      />
                    </div>
                    <span className="text-sm">{(selectedCitation.score * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Content / 内容</p>
                  <p className="text-xs bg-white p-2 rounded border mt-1">
                    {selectedCitation.content}
                  </p>
                </div>
              </div>
            </div>
          )}
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
