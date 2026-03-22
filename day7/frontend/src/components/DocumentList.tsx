/**
 * Document list component
 * 文档列表组件
 */

import { useState, useEffect } from 'react'
import { getDocuments, deleteDocument, DocumentInfo } from '../api/client'

interface DocumentListProps {
  onRefresh?: () => void
}

function DocumentList({ onRefresh }: DocumentListProps) {
  // List of documents
  // 文档列表
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  // Loading state
  // 加载状态
  const [loading, setLoading] = useState(true)
  // Error message
  // 错误消息
  const [error, setError] = useState<string | null>(null)
  // Deleting document ID
  // 正在删除的文档 ID
  const [deletingId, setDeletingId] = useState<string | null>(null)

  /**
   * Load documents from API
   * 从 API 加载文档
   */
  const loadDocuments = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getDocuments()
      setDocuments(response.documents)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(`Failed to load documents: ${errorMessage} / 加载文档失败: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle document deletion
   * 处理文档删除
   */
  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document? / 确定要删除此文档吗？')) {
      return
    }

    setDeletingId(documentId)
    try {
      await deleteDocument(documentId)
      // Remove from local state
      // 从本地状态中移除
      setDocuments(documents.filter(doc => doc.id !== documentId))
      // Notify parent if needed
      // 如需要通知父组件
      if (onRefresh) {
        onRefresh()
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      alert(`Failed to delete document: ${errorMessage} / 删除文档失败: ${errorMessage}`)
    } finally {
      setDeletingId(null)
    }
  }

  // Load documents on mount
  // 挂载时加载文档
  useEffect(() => {
    loadDocuments()
  }, [])

  /**
   * Format date for display
   * 格式化日期用于显示
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-center text-gray-500">
            Loading documents... / 正在加载文档...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            Documents / 文档列表
          </h2>
          <button
            onClick={loadDocuments}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            🔄 Refresh / 刷新
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md mb-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-4xl mb-2">📭</p>
            <p>No documents uploaded yet. / 尚未上传文档。</p>
            <p className="text-sm mt-1">
              Go to Upload tab to add documents. / 转到上传标签页添加文档。
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-4">Filename / 文件名</th>
                  <th className="text-left py-2 px-4">Chunks / 分块数</th>
                  <th className="text-left py-2 px-4">Uploaded / 上传时间</th>
                  <th className="text-right py-2 px-4">Actions / 操作</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <span className="font-medium">{doc.filename}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                        {doc.chunk_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-sm">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${
                          deletingId === doc.id
                            ? 'bg-gray-100 text-gray-400'
                            : 'bg-red-100 text-red-600 hover:bg-red-200'
                        }`}
                      >
                        {deletingId === doc.id ? (
                          'Deleting... / 删除中...'
                        ) : (
                          '🗑️ Delete / 删除'
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary */}
        {/* 摘要 */}
        {documents.length > 0 && (
          <div className="mt-4 pt-4 border-t text-sm text-gray-500">
            Total: {documents.length} document(s),{' '}
            {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)} chunk(s)
            <br />
            总计: {documents.length} 个文档,{' '}
            {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)} 个分块
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentList
