/**
 * User Management Panel Component
 * 用户管理面板组件
 *
 * Day 6: Security & Governance
 * Day 6： 安全与治理
 */

import React, { useState, useEffect } from 'react'
import { getUsers, updateUserRole, deactivateUser, UserInfo } from '../api/client'

interface UserManagementPanelProps {
  currentUser: UserInfo
}

const UserManagementPanel: React.FC<UserManagementPanelProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<UserInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Load users on mount
  // 加载时获取用户列表
  useEffect(() => {
    loadUsers()
  }, [])

  // Load users from API
  // 从 API 加载用户
  const loadUsers = async () => {
    setLoading(true)
    try {
      const response = await getUsers()
      setUsers(response.users)
    } catch (err) {
      setError('Failed to load users')
      // 加载用户失败
    } finally {
      setLoading(false)
    }
  }

  // Handle role change
  // 处理角色更改
  const handleRoleChange = async (userId: string, newRole: string) => {
    setError('')
    setSuccess('')

    try {
      await updateUserRole(userId, { role: newRole as 'admin' | 'user' | 'viewer' })
      setSuccess(`User role updated to ${newRole}`)
      // 用户角色已更新为 ${newRole}
      await loadUsers()
    } catch (err) {
      setError('Failed to update user role')
      // 更新用户角色失败
    }
  }

  // Handle user deactivation
  // 处理用户停用
  const handleDeactivate = async (userId: string) => {
    if (userId === currentUser.id) {
      setError('Cannot deactivate yourself')
      // 不能停用自己
      return
    }

    if (!window.confirm('Are you sure you want to deactivate this user?')) {
      // 确定要停用此用户吗？
      return
    }

    setError('')
    setSuccess('')

    try {
      await deactivateUser(userId)
      setSuccess('User deactivated successfully')
      // 用户已成功停用
      await loadUsers()
    } catch (err) {
      setError('Failed to deactivate user')
      // 停用用户失败
    }
  }

  // Get role badge color
  // 获取角色徽章颜色
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800'
      case 'user':
        return 'bg-blue-100 text-blue-800'
      case 'viewer':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Get status badge color
  // 获取状态徽章颜色
  const getStatusBadgeColor = (isActive: boolean) => {
    return isActive
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading users...</div>
        <div className="text-gray-500 ml-2">加载用户中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">
        User Management / 用户管理
      </h2>

      {/* Error message / 错误消息 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Success message / 成功消息 */}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Users table / 用户表格 */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User / 用户
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email / 邮箱
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role / 角色
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status / 状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions / 操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.username}
                        {user.id === currentUser.id && (
                          <span className="ml-2 text-xs text-gray-500">(You)</span>
                        )}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(user.role)}`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(user.is_active)}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {user.id !== currentUser.id && (
                    <div className="flex space-x-2">
                      {/* Role selector / 角色选择器 */}
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className="text-xs border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="admin">Admin</option>
                        <option value="user">User</option>
                        <option value="viewer">Viewer</option>
                      </select>

                      {/* Deactivate button / 停用按钮 */}
                      {user.is_active && (
                        <button
                          onClick={() => handleDeactivate(user.id)}
                          className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded hover:bg-red-200"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User count / 用户数量 */}
      <div className="mt-4 text-sm text-gray-500">
        Total users: {users.length} / 总用户数: {users.length}
      </div>
    </div>
  )
}

export default UserManagementPanel
