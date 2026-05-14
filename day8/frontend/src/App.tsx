/**
 * Main App component for Day 8 RAG Application
 * Day 8 RAG 应用的主 App 组件
 *
 * Day 8 Enhancement: LLM Wiki - Knowledge Compilation
 * Day 8 增强： LLM Wiki - 知识编译
 */

import { useState, useEffect } from 'react'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import ChatInterface from './components/ChatInterface'
import EvaluationPanel from './components/EvaluationPanel'
import LoginPanel from './components/LoginPanel'
import AuditPanel from './components/AuditPanel'
import WikiBrowser from './components/WikiBrowser'
import { UserInfo } from './api/client'

import { healthCheck as apiHealthCheck } from './api/client'

// Tab type definition
// Tab 类型定义
type TabType = 'upload' | 'documents' | 'chat' | 'wiki' | 'evaluation' | 'audit'

function App() {
  // Current active tab
  // 当前活动的标签页
  const [activeTab, setActiveTab] = useState<TabType>('upload')
  // Refresh key for document list
  // 文档列表的刷新键
  const [refreshKey, setRefreshKey] = useState(0)

  // Authentication state
  // 认证状态
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null)

  // System status for performance monitoring
  // 系统状态，性能监控
  const [systemStatus, setSystemStatus] = useState<any>(null)

  // Check for existing auth on mount
  // 挂载时检查现有认证
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userStr = localStorage.getItem('user_info')

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as UserInfo
        setCurrentUser(user)
        setIsAuthenticated(true)
      } catch {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_info')
      }
    }
  }, [])

  // Fetch system status on mount
  // 挂载时获取系统状态
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const health = await apiHealthCheck()
        setSystemStatus(health)
      } catch (error) {
        console.error('Failed to fetch system status:', error)
      }
    }
    fetchStatus()
  }, [])

  /**
   * Handle successful login
   * 处理成功登录
   */
  const handleLoginSuccess = (user: UserInfo, token: string) => {
    setCurrentUser(user)
    setIsAuthenticated(true)
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_info', JSON.stringify(user))
  }

  /**
   * Handle logout
   * 处理登出
   */
  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
    setCurrentUser(null)
    setIsAuthenticated(false)
  }

  /**
   * Handle document upload success
   * 处理文档上传成功
   */
  const handleUploadSuccess = () => {
    // Refresh document list
    // 刷新文档列表
    setRefreshKey(prev => prev + 1)
    // Switch to documents tab
    // 切换到文档标签页
    setActiveTab('documents')
  }

  // Show login panel if not authenticated
  // 如果未认证则显示登录面板
  if (!isAuthenticated) {
    return <LoginPanel onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      {/* 头部 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Step-by-Step RAG
              <span className="ml-2 text-sm font-normal text-gray-500">
                Day 8: LLM Wiki / 知识编译
              </span>
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Knowledge Compilation: Document → Wiki Pages, Semantic Search, Cross-referencing
              <br />
              知识编译：文档 → Wiki 页面，语义搜索，交叉引用
            </p>
          </div>

          {/* User info and logout / 用户信息和登出 */}
          <div className="flex items-center space-x-4">
            {/* System Status / 系统状态 */}
            {systemStatus && (
              <div className="text-right text-xs text-gray-500">
                <p>v{systemStatus.version}</p>
                <p className="flex items-center justify-end gap-1">
                  <span className={`w-2 h-2 rounded-full ${
                    systemStatus.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                  }`}></span>
                  {systemStatus.status}
                </p>
              </div>
            )}

            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">
                {currentUser?.username}
              </p>
              <p className="text-xs text-gray-500">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  currentUser?.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                  currentUser?.role === 'user' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {currentUser?.role}
                </span>
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
            >
              Logout / 登出
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      {/* 导航标签 */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'upload'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Upload / 上传
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Documents / 文档
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chat / 问答
            </button>
            <button
              onClick={() => setActiveTab('wiki')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'wiki'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Wiki / 知识库
            </button>
            <button
              onClick={() => setActiveTab('evaluation')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'evaluation'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Evaluation / 评估
            </button>
            {/* Audit tab - admin only / 审计标签页 - 仅管理员 */}
            {currentUser?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('audit')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'audit'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Audit / 审计
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'upload' && (
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        )}
        {activeTab === 'documents' && (
          <DocumentList
            key={refreshKey}
            onRefresh={() => setRefreshKey(prev => prev + 1)}
          />
        )}
        {/* Fix: Use CSS hidden instead of conditional rendering to preserve ChatInterface state across tab switches */}
        {/* 修复： 使用 CSS 隐藏替代条件渲染，保持 ChatInterface 在标签切换时的状态 */}
        <div className={activeTab !== 'chat' ? 'hidden' : ''}>
          <ChatInterface />
        </div>
        {/* Day 8: Wiki Knowledge Browser */}
        {/* Day 8： Wiki 知识浏览器 */}
        {activeTab === 'wiki' && (
          <WikiBrowser />
        )}
        {activeTab === 'evaluation' && (
          <div className="space-y-6">
            {/* Day 8: Wiki Feature Highlight */}
            {/* Day 8： Wiki 功能亮点 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                Day 8: LLM Wiki Knowledge Compilation
                Day 8： LLM Wiki 知识编译
              </h2>
              <p className="text-gray-600 mb-4">
                New Wiki system that compiles documents into structured knowledge pages.
                <br />
                新的 Wiki 系统，将文档编译为结构化的知识页面。
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="bg-green-50 p-3 rounded">
                  <p className="font-medium text-green-700">Wiki Generation</p>
                  <p className="text-green-600">LLM 自动生成 Wiki 页面</p>
                </div>
                <div className="bg-blue-50 p-3 rounded">
                  <p className="font-medium text-blue-700">Semantic Search</p>
                  <p className="text-blue-600">基于向量语义搜索 Wiki</p>
                </div>
                <div className="bg-purple-50 p-3 rounded">
                  <p className="font-medium text-purple-700">Cross-referencing</p>
                  <p className="text-purple-600">自动交叉引用关联页面</p>
                </div>
              </div>
            </div>

            {/* Day 5: Evaluation panel */}
            {/* Day 5： 评估面板 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                RAG Evaluation Dashboard / RAG 评估仪表板
              </h2>
              <EvaluationPanel
                question="What is RAG?"
                answer="RAG (Retrieval-Augmented Generation) is a technique..."
                contexts={["Context about RAG systems..."]}
              />
            </div>
          </div>
        )}
        {activeTab === 'audit' && currentUser?.role === 'admin' && (
          <AuditPanel />
        )}
      </main>

      {/* Footer */}
      {/* 页脚 */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          Step-by-Step RAG Tutorial - Day 8 (LLM Wiki - Knowledge Compilation)
          <br />
          循序渐进 RAG 教程 - Day 8（LLM Wiki - 知识编译）
        </div>
      </footer>
    </div>
  )
}

export default App
