/**
 * Login Panel Component
 * 登录面板组件
 *
 * Day 6: Security & Governance
 * Day 6： 安全与治理
 */

import React, { useState } from 'react'
import { login, register, UserInfo } from '../api/client'

interface LoginPanelProps {
  onLoginSuccess: (user: UserInfo, token: string) => void
}

const LoginPanel: React.FC<LoginPanelProps> = ({ onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Handle login form submission
  // 处理登录表单提交
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await login({ username, password })

      // Store token
      // 存储 token
      localStorage.setItem('auth_token', response.access_token)

      // Create user info
      // 创建用户信息
      const user: UserInfo = {
        id: response.user_id,
        username: response.username,
        email: '',
        role: response.role as 'admin' | 'user' | 'viewer',
        is_active: true,
      }
      localStorage.setItem('user_info', JSON.stringify(user))

      onLoginSuccess(user, response.access_token)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Login failed. Please check your credentials.'
      )
      // 登录失败。请检查您的凭据。
    } finally {
      setLoading(false)
    }
  }

  // Handle registration form submission
  // 处理注册表单提交
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate passwords match
    // 验证密码匹配
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      // 密码不匹配
      return
    }

    // Validate password length
    // 验证密码长度
    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      // 密码必须至少 8 个字符
      return
    }

    setLoading(true)

    try {
      const response = await register({
        username,
        email,
        password,
        role: 'user',
      })

      // Store token
      // 存储 token
      localStorage.setItem('auth_token', response.access_token)

      // Create user info
      // 创建用户信息
      const user: UserInfo = {
        id: response.user_id,
        username: response.username,
        email,
        role: response.role as 'admin' | 'user' | 'viewer',
        is_active: true,
      }
      localStorage.setItem('user_info', JSON.stringify(user))

      onLoginSuccess(user, response.access_token)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Registration failed. Please try again.'
      )
      // 注册失败。请重试。
    } finally {
      setLoading(false)
    }
  }

  // Handle tab switch
  // 处理标签切换
  const handleTabSwitch = (loginMode: boolean) => {
    setIsLogin(loginMode)
    setError('')
    setPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md">
        {/* Header / 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-800">
            Step-by-Step RAG
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Day 6: Security & Governance
            <br />
            Day 6： 安全与治理
          </p>
        </div>

        {/* Tab Buttons / 标签按钮 */}
        <div className="flex mb-6">
          <button
            type="button"
            onClick={() => handleTabSwitch(true)}
            className={`flex-1 py-2 text-center font-medium rounded-l-lg ${
              isLogin
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Login / 登录
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch(false)}
            className={`flex-1 py-2 text-center font-medium rounded-r-lg ${
              !isLogin
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Register / 注册
          </button>
        </div>

        {/* Error Message / 错误消息 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Login Form / 登录表单 */}
        {isLogin ? (
          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Username / 用户名
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Password / 密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Logging in...' : 'Login / 登录'}
            </button>
          </form>
        ) : (
          /* Register Form / 注册表单 */
          <form onSubmit={handleRegister}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Username / 用户名
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Email / 邮箱
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter email"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Password / 密码 (min 8 chars / 至少 8 字符)
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
                required
                minLength={8}
              />
            </div>

            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-medium mb-2">
                Confirm Password / 确认密码
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Confirm password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Registering...' : 'Register / 注册'}
            </button>
          </form>
        )}

        {/* Default credentials hint / 默认凭据提示 */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Default Admin / 默认管理员:</strong>
            <br />
            Username: <code className="bg-blue-100 px-1">admin</code>
            <br />
            Password: <code className="bg-blue-100 px-1">admin123</code>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPanel
