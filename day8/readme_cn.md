# 循序渐进 RAG 教程

## Day 7: 生产就绪

完整的、可投入生产的 RAG（检索增强生成）系统，通过 7 天循序渐进构建。

---

## 概述

本项目演示如何循序渐进地构建企业级 RAG 系统，每天添加新功能，同时保持完整可运行的应用。

### 每日进度

| Day | 主题 | 核心功能 |
|-----|------|----------|
| Day 1 | 最小化 RAG | 文档上传、向量搜索、基础问答 |
| Day 2 | 数据预处理 | 多格式解析、智能分块 |
| Day 3 | 检索优化 | 混合检索（向量 + BM25）、重排序 |
| Day 4 | 生成增强 | 流式输出、引用溯源、置信度评分 |
| Day 5 | 评估与可观测性 | RAGAS 评估、请求追踪 |
| Day 6 | 安全与治理 | JWT 认证、ACL 权限、审计日志 |
| **Day 7** | **生产就绪** | **缓存、指标监控、Docker 部署** |

---

## Day 7 功能

### 性能优化
- **缓存层**: 内存 TTL 缓存，可选 Redis 支持
- **性能指标**: 延迟跟踪 (P50, P95, P99)、错误率
- **重试逻辑**: 指数退避，提高 API 调用弹性
- **速率限制**: 请求速率保护

### Docker 部署
- **多阶段构建**: 优化的镜像大小
- **Docker Compose**: 一键部署
- **健康检查**: 容器级监控
- **卷持久化**: 重启后数据持久化

### 监控与可观测性
- **性能仪表板**: 通过 `/metrics` 端点实时监控
- **缓存统计**: 通过 `/cache/stats` 查看命中率
- **请求计时**: 所有响应包含 X-Process-Time-Ms 头

---

## 快速开始

### 前提条件
- Docker 和 Docker Compose
- OpenAI API 密钥（或兼容 API）

### 1. 克隆并配置

```bash
# 克隆仓库
git clone <repository-url>
cd step-by-step-rag/day7

# 创建环境文件
cat > .env << EOF
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
JWT_SECRET_KEY=change-me-in-production
EOF
```

### 2. 使用 Docker Compose 启动

```bash
# 启动所有服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问应用

| 服务 | URL |
|---------|-----|
| 前端 | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| 指标 | http://localhost:8000/metrics |
| 缓存统计 | http://localhost:8000/cache/stats |

### 4. 登录

默认凭据：
- 用户名: `admin`
- 密码: `admin123`

**⚠️ 生产环境请更改这些凭据！**

---

## 开发环境设置

### 后端（不使用 Docker）

```bash
cd day7/backend

# 使用 uv 安装依赖
pip install uv
uv pip install -e .

# 设置环境变量
export OPENAI_API_KEY=your-api-key
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db

# 运行服务器
uvicorn src.main:app --reload --port 8000
```

### 前端（不使用 Docker）

```bash
cd day7/frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 生产构建
npm run build
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  上传    │ │  对话    │ │   评估   │ │   审计   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  中间件层                             │   │
│  │  • 指标  • 速率限制  • 认证  • 缓存                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  服务层                               │   │
│  │  • RAG 管道  • 评估  • 安全                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │PostgreSQL│ │  Redis   │ │OpenAI API│                    │
│  │ pgvector │ │  缓存    │ │   LLM    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 配置

### 环境变量

```bash
# API 配置
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 数据库
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/rag_db

# 缓存
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://redis:6379/0

# 安全
JWT_SECRET_KEY=your-secret-key
AUTH_ENABLED=true

# 指标
METRICS_ENABLED=true

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

---

## API 端点

### 认证
| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/auth/register` | 注册新用户 |
| POST | `/auth/login` | 登录并获取 JWT token |
| POST | `/auth/logout` | 登出 |
| GET | `/auth/me` | 获取当前用户信息 |

### 文档
| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/documents/upload` | 上传文档 |
| GET | `/documents` | 列出文档 |
| DELETE | `/documents/{id}` | 删除文档 |

### 对话
| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/chat` | RAG 对话（非流式） |
| POST | `/chat/stream` | 流式对话（SSE） |

### 评估
| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/evaluation/rag` | 运行 RAGAS 评估 |
| POST | `/evaluation/retrieval` | 获取检索指标 |

### 生产功能 (Day 7)
| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/metrics` | 性能指标 |
| GET | `/cache/stats` | 缓存统计 |
| GET | `/health` | 详细健康检查 |

---

## 性能特性

### 缓存
```python
# 使用装饰器自动缓存查询结果
@cache_service.cached_query("embedding")
async def get_embedding(text: str) -> list:
    # 仅在缓存未命中时执行
    return await embedding_service.embed(text)
```

### 重试逻辑
```python
# 带有指数退避的自动重试
@with_retry(max_attempts=3, exception_types=(ConnectionError,))
async def call_external_api():
    # 失败时自动重试
    return await api_client.request()
```

### 性能跟踪
```python
# 跟踪函数性能
@track_performance("vector_search")
async def search_vectors(query: str) -> list:
    # 延迟和成功率自动记录
    return await vector_store.search(query)
```

---

## 监控

### 可用指标
- **延迟**: 平均值、P50、P95、P99
- **错误率**: 每个操作的错误跟踪
- **吞吐量**: 每秒请求数
- **缓存命中率**: 缓存有效性

### 示例指标响应
```json
{
  "enabled": true,
  "operations": {
    "POST /chat": {
      "total_requests": 150,
      "errors": 2,
      "error_rate": 0.013,
      "avg_latency_ms": 450.2,
      "p50_latency_ms": 380.0,
      "p95_latency_ms": 890.0,
      "p99_latency_ms": 1200.0
    }
  }
}
```

---

## 安全

### 默认凭据（仅限开发环境）
- 用户名: `admin`
- 密码: `admin123`

### 生产安全检查清单
- [ ] 更改 JWT 密钥
- [ ] 更改默认管理员密码
- [ ] 启用 HTTPS
- [ ] 配置 CORS 源
- [ ] 设置速率限制
- [ ] 启用审计日志

---

## 许可证

MIT License

---

## 贡献

欢迎贡献！请先阅读贡献指南。

---

## 支持

如有问题和疑问，请提交 GitHub issue。
