# Day 1: Minimal RAG Implementation
# Day 1: 最小化 RAG 实现

A simple but complete RAG (Retrieval-Augmented Generation) system.
一个简单但完整的 RAG（检索增强生成）系统。

## Features / 功能

- **Document Upload**: Upload text files (.txt)
- **文档上传**: 上传文本文件 (.txt)
- **Automatic Chunking**: Split documents into manageable chunks
- **自动分块**: 将文档分割为可管理的块
- **Vector Storage**: Store embeddings in pgvector
- **向量存储**: 在 pgvector 中存储嵌入
- **Question Answering**: Ask questions based on uploaded documents
- **问答**: 基于上传的文档提问

## Architecture / 架构

```
day1/
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI entry point / FastAPI 入口
│   │   ├── config.py         # Configuration / 配置
│   │   ├── routers/
│   │   │   ├── documents.py  # Document API / 文档 API
│   │   │   └── chat.py       # Chat API / 聊天 API
│   │   ├── services/
│   │   │   ├── embedding.py  # Embedding service / 嵌入服务
│   │   │   ├── llm.py        # LLM service / LLM 服务
│   │   │   └── vector_store.py # Vector store / 向量存储
│   │   └── models/
│   │       └── schemas.py    # Data models / 数据模型
│   ├── test/
│   │   └── test_main.py      # Test cases / 测试用例
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx            # Main app component / 主应用组件
    │   ├── main.tsx           # Entry point / 入口
    │   ├── index.css          # Styles / 样式
    │   ├── api/
    │   │   └── client.ts      # API client / API 客户端
    │   └── components/
    │       ├── DocumentUpload.tsx
    │       ├── DocumentList.tsx
    │       └── ChatInterface.tsx
    ├── package.json
    └── vite.config.ts
```

## Prerequisites / 前提条件

1. **PostgreSQL with pgvector**: Database for vector storage
   **带有 pgvector 的 PostgreSQL**: 向量存储的数据库
2. **Python 3.10+**: Backend runtime
   **Python 3.10+**: 后端运行时
3. **Node.js 18+**: Frontend runtime
   **Node.js 18+**: 前端运行时
4. **OpenAI API Key** (or compatible): For embeddings and LLM
   **OpenAI API Key** (或兼容): 用于嵌入和 LLM

## Quick Start / 快速开始

### 1. Setup Database / 设置数据库

```bash
# Install PostgreSQL and enable pgvector
# 安装 PostgreSQL 并启用 pgvector
CREATE DATABASE rag_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Setup Backend / 设置后端

```bash
cd day1/backend

# Create virtual environment
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
# 安装依赖
pip install -r requirements.txt

# Configure environment
# 配置环境
cp .env.example .env
# Edit .env with your settings
# 编辑 .env 填入你的设置

# Run server
# 运行服务器
cd src
python main.py
```

### 3. Setup Frontend / 设置前端

```bash
cd day1/frontend

# Install dependencies
# 安装依赖
npm install

# Run development server
# 运行开发服务器
npm run dev
```

### 4. Access the Application / 访问应用

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## API Endpoints / API 端点

| Method | Endpoint | Description / 描述 |
|--------|----------|-------------------|
| POST | `/documents/upload` | Upload a document / 上传文档 |
| GET | `/documents/list` | List all documents / 列出所有文档 |
| DELETE | `/documents/{id}` | Delete a document / 删除文档 |
| POST | `/chat/ask` | Ask a question / 提问 |
| GET | `/health` | Health check / 健康检查 |

## Testing / 测试

```bash
cd day1/backend
pip install -r test/pytest.ini
pytest test/test_main.py -v
```

## Next Steps / 下一步

After completing Day 1, proceed to Day 2 for:
完成 Day 1 后，继续 Day 2：
- Multi-format document parsing (PDF, Word)
- 多格式文档解析 (PDF, Word)
- Advanced chunking strategies
- 高级分块策略
- Metadata extraction
- 元数据提取

## Notes / 注意

- Day 1 only supports .txt files
- Day 1 仅支持 .txt 文件
- Conversation history is stored in memory (Day 6 will add database storage)
- 对话历史存储在内存中（Day 6 将添加数据库存储）
- No authentication yet (Day 6)
- 尚无认证（Day 6）
