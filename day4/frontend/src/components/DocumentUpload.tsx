/**
 * Document upload component
 * 文档上传组件
 */

import { useState, useRef } from 'react'
import { uploadDocument } from '../api/client'

interface DocumentUploadProps {
  onUploadSuccess: () => void
}

function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  // Selected file
  // 选中的文件
  const [file, setFile] = useState<File | null>(null)
  // Upload status
  // 上传状态
  const [uploading, setUploading] = useState(false)
  // Error message
  // 错误消息
  const [error, setError] = useState<string | null>(null)
  // Success message
  // 成功消息
  const [success, setSuccess] = useState<string | null>(null)
  // File input ref
  // 文件输入引用
  const fileInputRef = useRef<HTMLInputElement>(null)

  /**
   * Handle file selection
   * 处理文件选择
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setSuccess(null)
    }
  }

  /**
   * Handle file upload
   * 处理文件上传
   */
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first. / 请先选择文件。')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await uploadDocument(file)
      setSuccess(
        `Document uploaded successfully! Created ${result.chunk_count} chunks. / ` +
        `文档上传成功！创建了 ${result.chunk_count} 个分块。`
      )
      setFile(null)
      // Reset file input
      // 重置文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      // Notify parent component
      // 通知父组件
      onUploadSuccess()
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(`Upload failed: ${errorMessage} / 上传失败: ${errorMessage}`)
    } finally {
      setUploading(false)
    }
  }

  /**
   * Handle drag and drop
   * 处理拖放
   */
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
      setError(null)
      setSuccess(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">
          Upload Document / 上传文档
        </h2>

        {/* Drop zone */}
        {/* 拖放区域 */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            file ? 'border-green-300 bg-green-50' : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".txt,.md,.pdf,.docx,.html"
            className="hidden"
          />

          {file ? (
            <div>
              <p className="text-lg font-medium text-green-700">
                ✓ {file.name}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          ) : (
            <div>
              <p className="text-gray-600">
                Click to select or drag and drop a file here
                <br />
                点击选择或拖放文件到此处
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Supported: .txt, .md, .pdf, .docx, .html / 支持: .txt, .md, .pdf, .docx, .html
              </p>
            </div>
          )}
        </div>

        {/* Error message */}
        {/* 错误消息 */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Success message */}
        {/* 成功消息 */}
        {success && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-700 text-sm">{success}</p>
          </div>
        )}

        {/* Upload button */}
        {/* 上传按钮 */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`mt-4 w-full py-2 px-4 rounded-md font-medium transition-colors ${
            !file || uploading
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {uploading ? (
            <span>
              Uploading... / 上传中...
            </span>
          ) : (
            <span>
              Upload Document / 上传文档
            </span>
          )}
        </button>

        {/* Instructions */}
        {/* 说明 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="font-medium text-blue-800 mb-2">
            Instructions / 说明
          </h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Upload documents: .txt, .md, .pdf, .docx, .html</li>
            <li>• 上传文档: .txt, .md, .pdf, .docx, .html</li>
            <li>• The system will automatically split the text into chunks</li>
            <li>• 系统将自动将文本分割为分块</li>
            <li>• After uploading, go to Chat tab to ask questions</li>
            <li>• 上传后，转到聊天标签页提问</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default DocumentUpload
