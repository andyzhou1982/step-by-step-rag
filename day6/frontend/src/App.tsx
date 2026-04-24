/**
 * Main App component for Day 6 RAG Application
 * Day 6 RAG 应用的主 App 组件
 *
 * Day 6 Enhancement: Security & Governance
 * Day 6 增强： 安全与治理
 */

import { useState, useEffect } from 'react'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import ChatInterface from './components/ChatInterface'
import EvaluationPanel from './components/EvaluationPanel'
import LoginPanel from './components/LoginPanel'
import AuditPanel from './components/AuditPanel'
import { UserInfo } from './api/client'

// Tab type definition
// Tab 类型定义
type TabType = 'upload' | 'documents' | 'chat' | 'evaluation' | 'audit'

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
                Day 6: Security & Governance / 安全与治理
              </span>
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              JWT Auth, Permissions, Audit Logs, Content Filtering
              <br />
              JWT 认证、权限控制、审计日志、内容过滤
            </p>
          </div>

          {/* User info and logout / 用户信息和登出 */}
          <div className="flex items-center space-x-4">
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
              📤 Upload Document / 上传文档
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📄 Documents / 文档列表
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💬 Chat / 问答
            </button>
            <button
              onClick={() => setActiveTab('evaluation')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'evaluation'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 Evaluation / 评估
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
                🔒 Audit / 审计
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
        {activeTab === 'evaluation' && (
          <div className="space-y-6">
            {/* Day 5: Standalone evaluation page */}
            {/* Day 5： 独立评估页面 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                📊 RAG Evaluation Dashboard / RAG 评估仪表板
              </h2>
              <p className="text-gray-600 mb-4">
                Use the evaluation panel below to assess RAG quality metrics.
                <br />
                使用下面的评估面板评估 RAG 质量指标。
              </p>
              <EvaluationPanel
                question="What is RAG?"
                answer="RAG (Retrieval-Augmented Generation) is a technique that combines retrieval with generation..."
                contexts={["Context about RAG systems..."]}
              />
            </div>

            {/* Feature descriptions */}
            {/* 功能描述 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-800 mb-2">
                  🎯 RAGAS Metrics / RAGAS 指标
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Faithfulness / 忠实度</li>
                  <li>• Answer Relevance / 答案相关性</li>
                  <li>• Context Precision / 上下文精确度</li>
                  <li>• Context Recall / 上下文召回率</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-800 mb-2">
                  🔍 Retrieval Metrics / 检索指标
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Recall@K</li>
                  <li>• Precision@K</li>
                  <li>• MRR (Mean Reciprocal Rank)</li>
                  <li>• NDCG (Normalized DCG)</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-800 mb-2">
                  🔐 JWT Authentication / JWT 认证
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Secure token-based auth / 安全的基于 token 的认证</li>
                  <li>• Role-based access control / 基于角色的访问控制</li>
                  <li>• Session management / 会话管理</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-800 mb-2">
                  🛡️ Content Filtering / 内容过滤
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• SQL injection detection / SQL 注入检测</li>
                  <li>• XSS prevention / XSS 防护</li>
                  <li>• Prompt injection detection / 提示注入检测</li>
                  <li>• PII masking / PII 遮罩</li>
                </ul>
              </div>
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
          Step-by-Step RAG Tutorial - Day 6
          <br />
          循序渐进 RAG 教程 - Day 6
        </div>
      </footer>
    </div>
  )
}

export default App
