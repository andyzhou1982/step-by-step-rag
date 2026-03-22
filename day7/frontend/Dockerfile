# Dockerfile for Step-by-Step RAG Frontend
# Step-by-Step RAG 前端 Dockerfile
# Day 7: Production Ready
# Day 7： 生产就绪

# Build stage
# 构建阶段
FROM node:20-alpine as build

# Set work directory
# 设置工作目录
WORKDIR /app

# Copy package files
# 复制包文件
COPY package*.json ./

# Install dependencies
# 安装依赖
RUN npm ci

# Copy source code
# 复制源代码
COPY . .

# Build the application
# 构建应用
RUN npm run build

# Production stage with nginx
# 生产阶段，使用 nginx
FROM nginx:alpine

# Copy custom nginx config
# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from build stage
# 从构建阶段复制构建文件
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
# 暴露端口
EXPOSE 80

# Health check
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
