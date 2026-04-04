/**
 * Evaluation Panel Component
 * 评估面板组件
 *
 * Day 5 Feature: Evaluation & Observability
 * Day 5 功能： 评估与可观测性
 *
 * Displays RAGAS evaluation metrics and retrieval quality scores
 * 显示 RAGAS 评估指标和检索质量分数
 *
 * Enhanced: Support selecting from QA history
 * 增强： 支持从问答历史选择
 */

import React, { useState, useEffect } from 'react'
import {
  EvaluationMetrics,
  evaluateRag,
  getMetricExplanations,
  MetricExplanations,
  getQAHistoryList,
  QAHistoryRecord,
} from '../api/client'

interface EvaluationPanelProps {
  question: string
  answer: string
  contexts: string[]
  autoEvaluate?: boolean
}

// Metric bar component showing score with color
// 显示分数和颜色的指标条组件
const MetricBar: React.FC<{
  label: string
  value: number
  explanation?: string
}> = ({ label, value, explanation }) => {
  // Determine color based on score
  // 根据分数确定颜色
  const getColor = (score: number): string => {
    if (score >= 0.7) return 'bg-green-500'
    if (score >= 0.4) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = (score: number): string => {
    if (score >= 0.7) return 'text-green-600'
    if (score >= 0.4) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-sm font-bold ${getTextColor(value)}`}>
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`${getColor(value)} h-2.5 rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(value * 100, 100)}%` }}
        />
      </div>
      {explanation && (
        <p className="text-xs text-gray-500 mt-1">{explanation}</p>
      )}
    </div>
  )
}

// History selection modal component
// 历史选择模态框组件
const HistoryModal: React.FC<{
  isOpen: boolean
  onClose: () => void
  onSelect: (record: QAHistoryRecord) => void
}> = ({ isOpen, onClose, onSelect }) => {
  const [records, setRecords] = useState<QAHistoryRecord[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 10

  useEffect(() => {
    if (isOpen) {
      loadHistory()
    }
  }, [isOpen, page])

  const loadHistory = async () => {
    setIsLoading(true)
    try {
      const response = await getQAHistoryList(page, pageSize)
      setRecords(response.records || [])
      setTotal(response.total || 0)
    } catch (e) {
      console.error('Failed to load QA history:', e)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">Select from History / 从历史选择</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-96 p-4">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
              <p className="mt-2 text-gray-500">Loading... / 加载中...</p>
            </div>
          ) : records.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No history records found / 未找到历史记录</p>
              <p className="text-sm mt-2">Ask some questions first! / 先问一些问题吧！</p>
            </div>
          ) : (
            <div className="space-y-3">
              {records.map((record) => (
                <div
                  key={record.id}
                  onClick={() => onSelect(record)}
                  className="p-3 border rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
                >
                  <p className="font-medium text-gray-800 truncate">
                    <span className="text-blue-600">Q:</span> {record.question}
                  </p>
                  <p className="text-sm text-gray-600 truncate mt-1">
                    <span className="text-green-600">A:</span> {record.answer.substring(0, 100)}...
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {record.contexts.length} contexts / 上下文 · {new Date(record.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with pagination */}
        {total > pageSize && (
          <div className="flex justify-between items-center p-4 border-t bg-gray-50">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-sm bg-gray-200 rounded disabled:opacity-50"
            >
              Previous / 上一页
            </button>
            <span className="text-sm text-gray-500">
              Page {page} of {Math.ceil(total / pageSize)}
            </span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page >= Math.ceil(total / pageSize)}
              className="px-3 py-1 text-sm bg-gray-200 rounded disabled:opacity-50"
            >
              Next / 下一页
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Main evaluation panel component
// 主评估面板组件
const EvaluationPanel: React.FC<EvaluationPanelProps> = ({
  question: initialQuestion,
  answer: initialAnswer,
  contexts: initialContexts,
  autoEvaluate = false,
}) => {
  const [question, setQuestion] = useState(initialQuestion)
  const [answer, setAnswer] = useState(initialAnswer)
  const [contexts, setContexts] = useState<string[]>(initialContexts)
  const [ragMetrics, setRagMetrics] = useState<EvaluationMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [explanations, setExplanations] = useState<MetricExplanations | null>(null)
  const [evalTime, setEvalTime] = useState<number>(0)
  const [showHistoryModal, setShowHistoryModal] = useState(false)

  // Update state when props change
  // 当 props 变化时更新状态
  useEffect(() => {
    setQuestion(initialQuestion)
    setAnswer(initialAnswer)
    setContexts(initialContexts)
  }, [initialQuestion, initialAnswer, initialContexts])

  // Load explanations on mount
  // 加载时获取指标说明
  useEffect(() => {
    const loadExplanations = async () => {
      try {
        const exp = await getMetricExplanations()
        setExplanations(exp)
      } catch (e) {
        console.error('Failed to load explanations:', e)
      }
    }
    loadExplanations()
  }, [])

  // Auto-evaluate if enabled
  // 如果启用则自动评估
  useEffect(() => {
    if (autoEvaluate && question && answer && contexts.length > 0) {
      handleEvaluate()
    }
  }, [autoEvaluate, question, answer, contexts])

  // Handle manual evaluation
  // 处理手动评估
  const handleEvaluate = async () => {
    if (!question || !answer || contexts.length === 0) {
      setError('Missing question, answer, or contexts / 缺少问题、答案或上下文')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await evaluateRag({
        question,
        answer,
        contexts,
      })
      setRagMetrics(response.rag_metrics)
      setEvalTime(response.evaluation_time_ms)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evaluation failed / 评估失败')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle history selection
  // 处理历史选择
  const handleHistorySelect = (record: QAHistoryRecord) => {
    setQuestion(record.question)
    setAnswer(record.answer)
    setContexts(record.contexts)
    setRagMetrics(null)
    setError(null)
    setShowHistoryModal(false)
  }

  // Get short explanation for a metric
  // 获取指标的简短说明
  const getShortExplanation = (metricKey: string): string => {
    if (!explanations?.rag_metrics?.[metricKey]) return ''
    const full = explanations.rag_metrics[metricKey]
    // Return first sentence only
    // 只返回第一句
    return full.split('。')[0] + '。'
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      {/* Header / 标题 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          📊 RAG Evaluation / RAG 评估
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowHistoryModal(true)}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors text-sm"
          >
            📋 From History / 从历史
          </button>
          {!autoEvaluate && (
            <button
              onClick={handleEvaluate}
              disabled={isLoading || !question || !answer || contexts.length === 0}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600
                         disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Evaluating... / 评估中...' : 'Evaluate / 评估'}
            </button>
          )}
        </div>
      </div>

      {/* Current evaluation content / 当前评估内容 */}
      <div className="mb-4 p-3 bg-gray-50 rounded text-sm">
        <p className="font-medium text-gray-700 truncate">
          <span className="text-blue-600">Q:</span> {question || 'No question / 无问题'}
        </p>
        <p className="text-gray-600 truncate mt-1">
          <span className="text-green-600">A:</span> {answer ? answer.substring(0, 100) + '...' : 'No answer / 无答案'}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {contexts.length} context chunks / 上下文分块
        </p>
      </div>

      {/* Loading state / 加载状态 */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          <span className="ml-3 text-gray-600">Running evaluation... / 正在评估...</span>
        </div>
      )}

      {/* Error state / 错误状态 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Results / 结果 */}
      {ragMetrics && !isLoading && (
        <div>
          {/* Overall Score / 总体分数 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg text-center">
            <span className="text-sm text-gray-500">Overall Score / 总体分数</span>
            <div className={`text-3xl font-bold ${
              ragMetrics.overall_score >= 0.7 ? 'text-green-600' :
              ragMetrics.overall_score >= 0.4 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {(ragMetrics.overall_score * 100).toFixed(1)}%
            </div>
            {evalTime > 0 && (
              <span className="text-xs text-gray-400">
                Evaluated in {(evalTime / 1000).toFixed(2)}s / 评估耗时
              </span>
            )}
          </div>

          {/* RAGAS Metrics / RAGAS 指标 */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
              RAGAS Metrics / RAGAS 指标
            </h4>

            <MetricBar
              label="Faithfulness / 忠实度"
              value={ragMetrics.faithfulness}
              explanation={getShortExplanation('faithfulness')}
            />

            <MetricBar
              label="Answer Relevance / 答案相关性"
              value={ragMetrics.answer_relevance}
              explanation={getShortExplanation('answer_relevance')}
            />

            <MetricBar
              label="Context Precision / 上下文精确度"
              value={ragMetrics.context_precision}
              explanation={getShortExplanation('context_precision')}
            />

            <MetricBar
              label="Context Recall / 上下文召回率"
              value={ragMetrics.context_recall}
              explanation={getShortExplanation('context_recall')}
            />
          </div>
        </div>
      )}

      {/* Empty state / 空状态 */}
      {!ragMetrics && !isLoading && !error && (
        <div className="text-center py-8 text-gray-500">
          <p>Click "Evaluate" to assess the answer quality / 点击"评估"评估答案质量</p>
          <p className="text-sm mt-2">
            Or select "From History" to evaluate past Q&A / 或选择"从历史"评估过去的问答
          </p>
        </div>
      )}

      {/* History selection modal / 历史选择模态框 */}
      <HistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        onSelect={handleHistorySelect}
      />
    </div>
  )
}

export default EvaluationPanel
