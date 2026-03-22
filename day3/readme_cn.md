# Day 1: 最小化 RAG 实现

一个简单但完整的 RAG（检索增强生成）系统。

## 功能特性

- **文档上传**: 上传文本文件 (.txt)
- **自动分块**: 将文档分割为可管理的块
- **向量存储**: 在 pgvector 中存储嵌入
- **问答**: 基于上传的文档提问

## 系统架构

```
day1/
├── backend/                 # 后端代码
│   ├── src/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── routers/         # API 路由
│   │   │   ├── documents.py # 文档 API
│   │   │   └── chat.py      # 聊天 API
│   │   ├── services/        # 业务服务
│   │   │   ├── embedding.py # 嵌入服务
│   │   │   ├── llm.py       # LLM 服务
│   │   │   └── vector_store.py # 向量存储
│   │   └── models/
│   │       └── schemas.py   # 数据模型
│   ├── test/                # 测试代码
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 环境变量示例
└── frontend/                # 前端代码
    ├── src/
    │   ├── App.tsx          # 主应用组件
    │   ├── main.tsx         # 入口文件
    │   ├── index.css        # 样式文件
    │   ├── api/
    │   │   └── client.ts    # API 客户端
    │   └── components/      # UI 组件
    │       ├── DocumentUpload.tsx  # 文档上传
    │       ├── DocumentList.tsx    # 文档列表
    │       └── ChatInterface.tsx   # 聊天界面
    ├── package.json         # Node 依赖
    └── vite.config.ts       # Vite 配置
```

## 前提条件

1. **PostgreSQL + pgvector**: 用于向量存储的数据库
2. **Python 3.10+**: 后端运行环境
3. **Node.js 18+**: 前端运行环境
4. **OpenAI API Key** (或兼容接口): 用于嵌入和 LLM

## 快速开始

### 1. 设置数据库

```bash
# 安装 PostgreSQL 并启用 pgvector 扩展
CREATE DATABASE rag_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. 设置后端

```bash
cd day1/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 运行服务器
cd src
python main.py
```

### 3. 设置前端

```bash
cd day1/frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

### 4. 访问应用

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/documents/upload` | 上传文档 |
| GET | `/documents/list` | 列出所有文档 |
| DELETE | `/documents/{id}` | 删除文档 |
| POST | `/chat/ask` | 提问 |
| GET | `/health` | 健康检查 |

## 运行测试

```bash
cd day1/backend
pip install -r test/pytest.ini
pytest test/test_main.py -v
```

## 下一步

完成 Day 1 后，继续 Day 2 将学习：
- 多格式文档解析 (PDF, Word)
- 智能分块策略
- 元数据提取

## 注意事项

- Day 1 仅支持 .txt 文件
- 对话历史存储在内存中（Day 6 将添加数据库存储）
- 尚无用户认证（Day 6）
