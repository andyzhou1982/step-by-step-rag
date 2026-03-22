/**
 * Main App component for Day 1 RAG Application
 * Day 1 RAG 应用的主 App 组件
 */

import { useState } from 'react'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import ChatInterface from './components/ChatInterface'

// Tab type definition
// Tab 类型定义
type TabType = 'upload' | 'documents' | 'chat'

function App() {
  // Current active tab
  // 当前活动的标签页
  const [activeTab, setActiveTab] = useState<TabType>('upload')
  // Refresh key for document list
  // 文档列表的刷新键
  const [refreshKey, setRefreshKey] = useState(0)

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      {/* 头部 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Step-by-Step RAG
            <span className="ml-2 text-sm font-normal text-gray-500">
              Day 1: Minimal Implementation / 最小化实现
            </span>
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Upload documents and ask questions based on their content
            <br />
            上传文档并基于其内容提问
          </p>
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
        {activeTab === 'chat' && <ChatInterface />}
      </main>

      {/* Footer */}
      {/* 页脚 */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          Step-by-Step RAG Tutorial - Day 1
          <br />
          循序渐进 RAG 教程 - Day 1
        </div>
      </footer>
    </div>
  )
}

export default App
