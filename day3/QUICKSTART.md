# Day 1 快速测试指南 / Day 1 Quick Test Guide

本指南将帮助你从零开始测试 Day 1 的 RAG 系统。
This guide will help you test the Day 1 RAG system from scratch.

## 前提条件 / Prerequisites

- Docker Desktop（用于运行 PostgreSQL + pgvector）
- Python 3.11+
- Node.js 18+
- uv（Python 包管理器）

---

## 步骤 1：启动数据库 / Step 1: Start Database

### 1.1 创建 Docker Compose 配置

创建文件 `day1/docker-compose.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: rag-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: rag_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 1.2 启动数据库容器

```bash
cd day1
docker-compose up -d
```

### 1.3 验证数据库连接

```bash
docker exec -it rag-postgres psql -U postgres -d rag_db -c "SELECT 1;"
```

---

## 步骤 2：配置环境变量 / Step 2: Configure Environment

### 2.1 编辑后端 .env 文件

编辑 `day1/backend/.env`：

```env
# OpenAI API Configuration
# 将下面的 your_api_key_here 替换为你的实际 API Key
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db

# Server Configuration
HOST=0.0.0.0
PORT=8000

# RAG Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=5
```

**注意**: 如果你使用的是国内模型服务（如通义千问、智谱等），需要修改 `OPENAI_API_BASE` 为对应的端点。

---

## 步骤 3：启动后端 / Step 3: Start Backend

### 3.1 进入后端目录

```bash
cd day1/backend
```

### 3.2 启动后端服务

```bash
uv run python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.3 验证后端启动

打开浏览器访问 http://localhost:8000/docs 查看 API 文档。

或者使用命令：

```bash
curl http://localhost:8000/health
```

期望输出：
```json
{"status":"healthy","database":"connected","version":"1.0.0"}
```

---

## 步骤 4：启动前端 / Step 4: Start Frontend

### 4.1 打开新终端窗口

### 4.2 进入前端目录

```bash
cd day1/frontend
```

### 4.3 启动前端开发服务器

```bash
npm run dev
```

### 4.4 访问前端

打开浏览器访问 http://localhost:3000

---

## 步骤 5：创建测试数据 / Step 5: Create Test Data

### 5.1 创建测试文档

创建文件 `day1/test_document.txt`：

```text
RAG系统介绍

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合了信息检索和生成式AI的技术。
它首先从知识库中检索相关文档，然后将这些文档作为上下文，让大语言模型生成更准确的回答。

RAG系统的主要组件包括：
1. 文档处理：将文档分块并转换为向量
2. 向量存储：使用向量数据库存储文档向量
3. 检索：根据问题检索最相关的文档
4. 生成：使用LLM基于检索结果生成回答

RAG的优势：
- 可以使用最新的知识，不受训练数据限制
- 减少LLM的幻觉问题
- 可以引用信息来源，提高可信度
- 更容易更新知识库

LangChain是一个流行的框架，用于构建RAG应用。它提供了：
- 多种文档加载器
- 多种文本分割器
- 多种向量存储后端
- 多种LLM接口

pgvector是PostgreSQL的向量扩展，可以存储和搜索向量数据。
它支持：
- 向量存储和索引
- 余弦相似度搜索
- 欧几里得距离搜索
- 与PostgreSQL的完整集成
```

### 5.2 上传测试文档

#### 方法一：通过前端上传

1. 在浏览器中打开 http://localhost:3000
2. 点击 "Upload Document" 标签
3. 选择 `test_document.txt` 文件上传
4. 等待上传成功提示

#### 方法二：通过 API 上传

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "accept: application/json" \
  -F "file=@day1/test_document.txt"
```

期望输出：
```json
{
  "document_id": "xxx-xxx-xxx",
  "filename": "test_document.txt",
  "chunk_count": 5,
  "created_at": "2025-03-22T..."
}
```

---

## 步骤 6：测试问答功能 / Step 6: Test Q&A

### 6.1 通过前端测试

1. 点击 "Chat" 标签
2. 输入问题：`什么是RAG系统？`
3. 点击发送
4. 查看回答和引用来源

### 6.2 通过 API 测试

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是RAG系统？"}'
```

期望输出：
```json
{
  "answer": "RAG（检索增强生成）是一种结合了信息检索和生成式AI的技术...",
  "sources": [
    {
      "document_id": "xxx",
      "filename": "test_document.txt",
      "content": "RAG（Retrieval-Augmented Generation...",
      "score": 0.85
    }
  ],
  "conversation_id": "xxx-xxx-xxx"
}
```

### 6.3 更多测试问题

试试这些问题：

1. `RAG系统有哪些主要组件？`
2. `LangChain提供了什么功能？`
3. `pgvector支持哪些功能？`
4. `RAG的优势是什么？`

---

## 步骤 7：验证文档管理 / Step 7: Verify Document Management

### 7.1 查看文档列表

```bash
curl http://localhost:8000/documents/list
```

### 7.2 删除文档

```bash
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

---

## 常见问题 / Troubleshooting

### Q1: 数据库连接失败

确保 Docker 容器正在运行：
```bash
docker ps | grep rag-postgres
```

如果未运行，启动它：
```bash
docker-compose up -d
```

### Q2: API Key 无效

检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确。

### Q3: 前端无法连接后端

确保后端在 8000 端口运行，前端在 3000 端口运行。

### Q4: 向量维度不匹配

确保使用相同的 embedding 模型。默认使用 `text-embedding-3-small`。

---

## 清理 / Cleanup

停止所有服务：

```bash
# 停止前端 (Ctrl+C in terminal)

# 停止后端 (Ctrl+C in terminal)

# 停止数据库
docker-compose down
```

---

## 下一步 / Next Steps

Day 1 完成后，你可以继续 Day 2 学习：
- 多格式文档解析 (PDF, Word)
- 智能分块策略
- 元数据提取
