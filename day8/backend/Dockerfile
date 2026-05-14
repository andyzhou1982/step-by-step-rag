# Dockerfile for Step-by-Step RAG Backend
# Step-by-Step RAG 后端 Dockerfile
# Day 7: Production Ready
# Day 7： 生产就绪

# Use Python 3.11 slim image
# 使用 Python 3.11 slim 镜像
FROM python:3.11-slim

# Set environment variables
# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
# 设置工作目录
WORKDIR /app

# Install system dependencies
# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
# 安装 uv 以实现更快的包管理
RUN pip install uv

# Copy project files
# 复制项目文件
COPY pyproject.toml .

# Install Python dependencies
# 安装 Python 依赖
RUN uv pip install --system -e .

# Copy application code
# 复制应用代码
COPY src/ ./src/

# Create non-root user for security
# 创建非 root 用户以提高安全性
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
# 暴露端口
EXPOSE 8000

# Health check
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# 运行应用
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
