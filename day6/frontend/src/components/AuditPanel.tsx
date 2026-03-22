/**
 * Audit Panel Component
 * 审计面板组件
 *
 * Day 6: Security & Governance
 * Day 6： 安全与治理
 */

import React, { useState, useEffect } from 'react'
import { getAuditLogs, getAuditSummary, AuditLogEntry, AuditSummaryResponse } from '../api/client'

const AuditPanel: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [summary, setSummary] = useState<AuditSummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState({
    action: '',
    resource_type: '',
    status: '',
  })

  // Load data on mount
  // 加载时获取数据
  useEffect(() => {
    loadData()
  }, [])

  // Load logs and summary
  // 加载日志和摘要
  const loadData = async () => {
    setLoading(true)
    try {
      const [logsResponse, summaryResponse] = await Promise.all([
        getAuditLogs({ limit: 100 }),
        getAuditSummary(7),
      ])
      setLogs(logsResponse.logs)
      setSummary(summaryResponse)
    } catch (err) {
      setError('Failed to load audit data')
      // 加载审计数据失败
    } finally {
      setLoading(false)
    }
  }

  // Apply filters
  // 应用过滤器
  const filteredLogs = logs.filter((log) => {
    if (filter.action && log.action !== filter.action) return false
    if (filter.resource_type && log.resource_type !== filter.resource_type) return false
    if (filter.status && log.status !== filter.status) return false
    return true
  })

  // Get action badge color
  // 获取操作徽章颜色
  const getActionBadgeColor = (action: string) => {
    if (action.includes('login') || action.includes('logout')) {
      return 'bg-blue-100 text-blue-800'
    }
    if (action.includes('create') || action.includes('upload')) {
      return 'bg-green-100 text-green-800'
    }
    if (action.includes('delete') || action.includes('deactivate')) {
      return 'bg-red-100 text-red-800'
    }
    if (action.includes('update') || action.includes('grant')) {
      return 'bg-yellow-100 text-yellow-800'
    }
    return 'bg-gray-100 text-gray-800'
  }

  // Get status badge color
  // 获取状态徽章颜色
  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Format timestamp
  // 格式化时间戳
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  // Get unique values for filters
  // 获取过滤器的唯一值
  const uniqueActions = [...new Set(logs.map((log) => log.action))]
  const uniqueResourceTypes = [...new Set(logs.map((log) => log.resource_type))]
  const uniqueStatuses = [...new Set(logs.map((log) => log.status))]

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading audit data...</div>
        <div className="text-gray-500 ml-2">加载审计数据中...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Error message / 错误消息 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Activity Summary / 活动摘要 */}
      {summary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            Activity Summary (Last {summary.period_days} days)
            <br />
            活动摘要（最近 {summary.period_days} 天）
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total actions / 总操作数 */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-blue-600">
                {summary.total_actions}
              </div>
              <div className="text-sm text-gray-600">
                Total Actions / 总操作数
              </div>
            </div>

            {/* Unique users / 唯一用户 */}
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-green-600">
                {summary.unique_users}
              </div>
              <div className="text-sm text-gray-600">
                Unique Users / 活跃用户
              </div>
            </div>

            {/* Top action / 最多操作 */}
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-lg font-bold text-purple-600">
                {Object.entries(summary.action_counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A'}
              </div>
              <div className="text-sm text-gray-600">
                Most Common Action / 最常见操作
              </div>
            </div>
          </div>

          {/* Action counts breakdown / 操作计数细分 */}
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Actions by Type / 按类型操作
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(summary.action_counts).map(([action, count]) => (
                <span
                  key={action}
                  className="px-3 py-1 bg-gray-100 rounded-full text-sm"
                >
                  {action}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs / 审计日志 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">
            Audit Logs / 审计日志
          </h2>

          {/* Refresh button / 刷新按钮 */}
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Refresh / 刷新
          </button>
        </div>

        {/* Filters / 过滤器 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <select
            value={filter.action}
            onChange={(e) => setFilter({ ...filter, action: e.target.value })}
            className="border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Actions / 所有操作</option>
            {uniqueActions.map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>

          <select
            value={filter.resource_type}
            onChange={(e) => setFilter({ ...filter, resource_type: e.target.value })}
            className="border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Resources / 所有资源</option>
            {uniqueResourceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            className="border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Status / 所有状态</option>
            {uniqueStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {/* Logs table / 日志表格 */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Time / 时间
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  User / 用户
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Action / 操作
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Resource / 资源
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status / 状态
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No audit logs found / 未找到审计日志
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {formatTime(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {log.username}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionBadgeColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      <span className="font-medium">{log.resource_type}</span>
                      {log.resource_id && (
                        <span className="text-xs text-gray-400 ml-1">
                          ({log.resource_id.slice(0, 8)}...)
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Results count / 结果计数 */}
        <div className="mt-4 text-sm text-gray-500">
          Showing {filteredLogs.length} of {logs.length} logs
          <br />
          显示 {filteredLogs.length} / {logs.length} 条日志
        </div>
      </div>
    </div>
  )
}

export default AuditPanel
