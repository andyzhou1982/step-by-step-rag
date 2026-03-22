/**
 * Main App component for Day 5 RAG Application
 * Day 5 RAG 应用的主 App 组件
 *
 * Day 5 Enhancement: Evaluation & Observability
 * Day 5 增强： 评估与可观测性
 */
import { useState } from 'react'
import DocumentUpload from './components/DocumentUpload'
import DocumentList from './components/DocumentList'
import ChatInterface from './components/ChatInterface'
import EvaluationPanel from './components/EvaluationPanel'

// Tab type definition
// Tab 类型定义
type TabType = 'upload' | 'documents' | 'chat' | 'evaluation'

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
              Day 5: Evaluation & Observability / 评估与可观测性
            </span>
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            RAGAS evaluation, retrieval metrics, request tracing, structured logging
            <br />
            RAGAS 评估、检索指标、请求追踪、结构化日志
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
                  🔗 Request Tracing / 请求追踪
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• OpenTelemetry integration / OpenTelemetry 集成</li>
                  <li>• Span-based tracing / 基于 Span 的追踪</li>
                  <li>• Performance timing / 性能计时</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-800 mb-2">
                  📝 Structured Logging / 结构化日志
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• JSON format logs / JSON 格式日志</li>
                  <li>• structlog integration / structlog 集成</li>
                  <li>• Context correlation / 上下文关联</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      {/* 页脚 */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          Step-by-Step RAG Tutorial - Day 5
          <br />
          循序渐进 RAG 教程 - Day 5
        </div>
      </footer>
    </div>
  )
}

export default App
