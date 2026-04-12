# Day 7 核心修改文档 / Day 7 Core Changes Documentation

本文档列出了 Day 7 相对于 Day 6 的核心修改及其原因。
This document lists the core changes from Day 6 to Day 7 and the reasons behind them.

---

## 重要说明 / Important Notice

Day 7 完全同步了 Day 6 的数据库迁移改进，包括：
Day 7 fully syncs with Day 6's database migration improvements, including:

- ✅ SQLAlchemy ORM 统一数据存储
- ✅ 用户数据存储在 PostgreSQL（替代 JSON 文件）
- ✅ 审计日志存储在 PostgreSQL
- ✅ 文档注册表使用 ORM
- ✅ 问答历史使用 ORM

详见 Day 6 CHANGES.md 的"数据库迁移增强"章节。
See "Database Migration Enhancement" section in Day 6 CHANGES.md for details.

---

## 1. 新增文件 / New Files

### `backend/src/services/cache_service.py`

**功能 / Purpose:**
缓存服务，支持内存缓存和可选的 Redis 分布式缓存。

**为什么新增 / Why Added:**
- Day 6 没有缓存机制
- Day 7 需要性能优化
- 减少重复计算和 API 调用

**核心类 / Core Classes:**
```python
class CacheService:
    """Cache service with TTL support / 带有 TTL 支持的缓存服务"""
    async def get(self, key: str) -> Optional[Any]
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool
    async def delete(self, key: str) -> bool
    async def clear(self) -> None
    async def get_stats(self) -> dict
    def cached_query(self, prefix: str)  # Decorator for caching / 缓存装饰器
```

---

### `backend/src/services/performance_service.py`

**功能 / Purpose:**
性能指标收集服务，用于监控和可观测性。

**为什么新增 / Why Added:**
- Day 6 没有性能监控
- Day 7 需要生产级监控
- 支持延迟跟踪和错误率监控

**核心类 / Core Classes:**
```python
class PerformanceMetrics:
    """Performance metrics collection service / 性能指标收集服务"""
    def record_latency(self, operation: str, latency_ms: float) -> None
    def record_request(self, operation: str, success: bool = True) -> None
    def get_percentile(self, operation: str, percentile: float) -> Optional[float]
    def get_average_latency(self, operation: str) -> Optional[float]
    def get_error_rate(self, operation: str) -> float
    def get_all_metrics(self) -> dict

def track_performance(operation: str):
    """Decorator to track function performance / 跟踪函数性能的装饰器"""
```

---

### `backend/Dockerfile`

**功能 / Purpose:**
后端 Docker 镜像构建文件。

**为什么新增 / Why Added:**
- Day 6 没有容器化配置
- Day 7 需要 Docker 部署支持
- 生产环境标准化

---

### `frontend/Dockerfile`

**功能 / Purpose:**
前端 Docker 镜像构建文件，使用多阶段构建。

**为什么新增 / Why Added:**
- Day 6 没有前端容器化
- Day 7 需要完整 Docker 支持
- 使用 nginx 作为生产服务器

---

### `frontend/nginx.conf`

**功能 / Purpose:**
Nginx 配置文件，用于前端静态文件服务和 API 代理。

---

### `docker-compose.yml`

**功能 / Purpose:**
完整的 Docker Compose 编排配置。

---

## 2. 修改的文件 / Modified Files

### `backend/pyproject.toml`

**修改内容 / Changes:**

```toml
version = "7.0.0"  # Updated from 6.0.0

# New dependencies / 新增依赖
# Production Optimization (Day 7)
"cachetools>=5.3.0",          # In-memory caching / 内存缓存
"redis>=5.0.0",               # Redis cache support / Redis 缓存支持
"tenacity>=8.2.0",            # Retry logic / 重试逻辑
"backoff>=2.2.0",             # Exponential backoff / 指数退避
"gunicorn>=21.0.0",           # Production WSGI server / 生产 WSGI 服务器
"prometheus-client>=0.19.0",  # Metrics collection / 指标收集
```

---

### `backend/src/config.py`

**新增配置 / Added Configuration:**

```python
# Production Configuration (Day 7)
# Cache Configuration
self.cache_enabled: bool = True
self.cache_ttl_seconds: int = 3600
self.cache_max_size: int = 1000
self.redis_url: Optional[str] = None

# Database Connection Pool
self.db_pool_min_size: int = 5
self.db_pool_max_size: int = 20

# Retry Configuration
self.retry_max_attempts: int = 3
self.retry_backoff_factor: float = 2.0

# Rate Limiting
self.rate_limit_enabled: bool = True
self.rate_limit_requests_per_minute: int = 60

# Metrics Configuration
self.metrics_enabled: bool = True
```

---

### `backend/src/main.py`

**修改内容 / Changes:**
- 更新版本到 7.0.0
- 添加缓存和性能指标服务
- 新增 `/metrics` 焦点
- 新增 `/cache/stats` 焦点

- 请求计时中间件

---

### `frontend/package.json`

**修改内容 / Changes:**
- 版本更新到 7.0.0

---

### `frontend/src/App.tsx`

**修改内容 / Changes:**
- 更新标题为 Day 7: Production Ready
- 添加系统状态显示
- 更新功能描述列表

---

## 3. 生产特性总结 / Production Features Summary

### 缓存 / Caching
| 特性 | 描述 |
|------|------|
| In-memory Cache | TTLCache with configurable size and TTL |
| Redis Support | Optional distributed caching |
| Query Caching | Decorator for automatic query result caching |

### 指标 / Metrics
| 指标类型 | 描述 |
|----------|------|
| Latency | Average and percentiles (P50, P95, P99) |
| Error Rate | Per-operation error tracking |
| Throughput | Request count tracking |

### Docker / Docker
| 组件 | 描述 |
|------|------|
| Backend Dockerfile | Multi-stage build with uv |
| Frontend Dockerfile | Multi-stage build with nginx |
| docker-compose.yml | Complete stack orchestration |
| Health Checks | Container-level health monitoring |

---

## 4. 环境变量 / Environment Variables

```bash
# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379/0

# Retry Configuration
RETRY_MAX_ATTEMPTS=3

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Metrics
METRICS_ENABLED=true
```

---

## 5. 快速启动 / Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 6. Bug 修复 / Bug Fix (2026-04-12)

### 文档删除失败修复

**问题 / Issue:** `vector_store.delete_document()` 使用 `filter={"filename": document_id}` 删除文档，但 `document_id` 是 UUID，`filename` 存储的是原始文件名，导致过滤器永远匹配不到任何文档，删除操作静默失败。

**修复 / Fix:**
- `store_document()`: 在创建文档前生成 `doc_id = str(uuid.uuid4())`，将 `doc_id` 写入每个 chunk 的 metadata，返回 `doc_id` 而非 PGVector 的 `ids[0]`
- `delete_document()`: 过滤条件改为 `filter={"doc_id": document_id}`

**修改文件 / Modified Files:**
- `backend/src/services/vector_store.py` (添加 `import uuid`；修改 `store_document` 和 `delete_document`)

### 健康检查端点修复

**问题 / Issue:** `health_check` 端点 `status` 硬编码为 "healthy"；只检查 `vector_store` 不检查 `db_service`；访问私有属性 `_vectorstore`；无实际连接活性测试；`day=6` 硬编码错误。

**修复 / Fix:**
- `database_service.py`: 添加 `health_check()` 方法执行 `SELECT 1` 验证连接活性
- `vector_store.py`: 添加公开的 `health_check()` 方法
- `main.py`: 重写端点，分别检查两个服务，不健康时返回 HTTP 503；`audit_service.get_logs` 包裹在 try/except 中；修复 `day=6` → `day=7`
- `schemas.py`: HealthResponse 字段从 `database: str` 拆分为 `db_status: str` + `vector_status: str`

**修改文件 / Modified Files:**
- `backend/src/services/database_service.py` (添加 `health_check` 方法)
- `backend/src/services/vector_store.py` (添加 `health_check` 方法)
- `backend/src/main.py` (重写健康检查端点，修复 day 值，安全化审计日志查询)
- `backend/src/models/schemas.py` (HealthResponse 字段拆分)

---

## 7. 访问服务 / Access Services

- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
