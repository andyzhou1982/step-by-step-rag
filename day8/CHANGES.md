# Day 8 核心修改文档 / Day 8 Core Changes Documentation

本文档列出了 Day 8 相对于 Day 7 的核心修改及其原因。
This document lists the core changes from Day 7 to Day 8 and the reasons behind them.

## 新增功能 / New Features

### 1. Wiki 知识编译系统 / Wiki Knowledge Compilation System

**概念提取 / Concept Extraction** (`services/concept_extractor.py`)
- LLM 从文档分块中提取核心概念（名称、描述、分类、重要性）
- 支持跨分块的概念合并与去重
- 小列表使用简单去重，大列表通过 LLM 智能合并

**Wiki 页面生成 / Wiki Page Generation** (`services/wiki_generator.py`)
- 为每个概念生成结构化 Markdown Wiki 页面
- 自动提取页面摘要
- 基于关键词匹配查找相关文档分块

**Wiki 存储与检索 / Wiki Storage & Retrieval** (`services/wiki_store.py`)
- Wiki 页面 CRUD 操作（SQLAlchemy ORM）
- 基于 pgvector 的语义搜索
- 关键词搜索作为回退方案
- 基于概念重叠的自动交叉引用
- 专用 `wiki_page_embeddings` 向量表

### 2. 数据库模型 / Database Models
- `WikiPage`: Wiki 页面（标题、内容、摘要、概念、来源追踪、版本、置信度）
- `WikiLink`: Wiki 页面间交叉引用链接（关系类型、置信度）

### 3. API 端点 / API Endpoints
- `POST /wiki/generate` - 从文档生成 Wiki 页面
- `GET /wiki/pages` - 列出所有 Wiki 页面
- `GET /wiki/pages/{id}` - 获取 Wiki 页面详情
- `POST /wiki/search` - 语义搜索 Wiki 页面
- `GET /wiki/concepts` - 列出所有概念
- `GET /wiki/stats` - Wiki 统计信息
- `DELETE /wiki/pages/{id}` - 删除 Wiki 页面

### 4. 前端 / Frontend
- `WikiBrowser.tsx`: Wiki 浏览器组件（统计面板、搜索、过滤、详情、生成）
- `App.tsx`: 新增 "Wiki / 知识库" 标签页
- `client.ts`: 新增 Wiki API 类型和函数

## 修改文件 / Modified Files

| File | Change |
|------|--------|
| `backend/src/models/database.py` | 添加 WikiPage, WikiLink ORM 模型 |
| `backend/src/models/schemas.py` | 添加 Wiki Pydantic 模型 |
| `backend/src/main.py` | 更新到 Day 8 版本，注册 Wiki 路由 |
| `backend/src/config.py` | 添加 Wiki 配置参数 |
| `frontend/src/App.tsx` | 添加 Wiki 标签页，Day 8 品牌 |
| `frontend/src/api/client.ts` | 添加 Wiki API 类型和函数 |
| `frontend/package.json` | 版本更新到 8.0.0 |

## 新增文件 / New Files

| File | Purpose |
|------|---------|
| `backend/src/services/concept_extractor.py` | 概念提取服务 |
| `backend/src/services/wiki_generator.py` | Wiki 页面生成服务 |
| `backend/src/services/wiki_store.py` | Wiki 存储与检索服务 |
| `backend/src/routers/wiki.py` | Wiki API 路由 |
| `frontend/src/components/WikiBrowser.tsx` | Wiki 浏览器前端组件 |
