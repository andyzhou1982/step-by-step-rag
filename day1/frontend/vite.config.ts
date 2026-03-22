import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration for React + TypeScript
// React + TypeScript 的 Vite 配置
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to backend
      // 将 API 请求代理到后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
