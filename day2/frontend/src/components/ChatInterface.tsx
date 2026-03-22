/**
 * Chat interface component for Q&A
 * 问答的聊天界面组件
 */

import { useState, useRef, useEffect } from 'react'
import { askQuestion, SourceReference } from '../api/client'

// Message type definition
// 消息类型定义
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceReference[]
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
          {messages.length > 0 && (
            <button
              onClick={handleClear}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              🗑️ Clear / 清除
            </button>
          )}
        </div>

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
                              <span className="text-gray-400">
                                Score: {source.score.toFixed(4)}
                              </span>
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
