"""
Main entry point for the RAG API
RAG API 的主入口

Day 2: Enhanced with multi-format document support
Day 2： 增强了多格式文档支持

Day 3: Added hybrid retrieval with BM25 indexing
Day 3： 添加了带 BM25 索引的混合检索

Day 6: Security & Governance - Authentication, Authorization, Audit
Day 6： 安全与治理 - 认证、授权、审计

Day 7: Production Optimization - Caching, Retry, Metrics
Day 7： 生产优化 - 缓存、重试、指标
"""

import traceback
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat, evaluation, qa_history
from routers import auth, permissions, audit
from services.vector_store import vector_store
from services.retrieval_service import retrieval_service
from services.document_registry import document_registry
from services.qa_history_service import qa_history_service
from services.audit_service import audit_service
from services.cache_service import cache_service
from services.performance_service import performance_service
from models.schemas import HealthResponse
from config import settings, setup_logging, get_logger

# Initialize logging system
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown
    应用生命周期管理器，用于启动和关闭
    """
    # Startup: Connect to databases
    # 启动: 连接数据库
    logger.info("Starting up... Connecting to databases.")
    await vector_store.connect()
    await document_registry.connect()
    await qa_history_service.connect()
    logger.info("Databases connected.")

    # Day 3: Build BM25 index from existing documents
    # Day 3： 从现有文档构建 BM25 索引
    logger.info("Building BM25 index...")
    try:
        documents = await vector_store.get_all_documents_for_bm25()
        if documents:
            retrieval_service.build_bm25_index(documents)
            logger.info(f"BM25 index built with {len(documents)} documents.")
        else:
            logger.info("No documents found for BM25 index.")
    except Exception as e:
        logger.warning(f"Failed to build BM25 index: {e}", exc_info=True)

    # Day 7: Initialize cache
    # Day 7： 初始化缓存
    if settings.cache_enabled:
        logger.info("Initializing cache service...")
        await cache_service.initialize()
        logger.info("Cache service initialized.")

    yield

    # Shutdown: Disconnect from databases
    # 关闭: 断开数据库连接
    logger.info("Shutting down... Disconnecting from databases.")
    await vector_store.disconnect()
    await document_registry.disconnect()
    await qa_history_service.disconnect()

    # Day 7: Clear cache
    # Day 7： 清空缓存
    if settings.cache_enabled:
        logger.info("Clearing cache...")
        await cache_service.clear()
        logger.info("Cache cleared.")

    logger.info("Databases disconnected.")


# Create FastAPI application
# 创建 FastAPI 应用
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
## Day 7: Production Optimization
## Day 7: 生产优化

A production-ready RAG (Retrieval-Augmented Generation) system with comprehensive features.
一个功能完整的生产级 RAG（检索增强生成）系统。

### Day 7 Features / Day 7 功能:
- **Caching**: In-memory and optional Redis caching
- **缓存**: 内存缓存和可选的 Redis 缓存
- **Retry Logic**: Exponential backoff for failed requests
- **重试逻辑**: 失败请求的指数退避重试
- **Performance Metrics**: Request timing and throughput monitoring
- **性能指标**: 请求计时和吞吐量监控
- **Request Timeout**: Configurable timeout for external API calls
- **请求超时**: 外部 API 调用的可配置超时

### Day 6 Features (Inherited) / Day 6 功能（继承）:
- **Authentication**: JWT-based user authentication
- **认证**: 基于 JWT 的用户认证
- **Authorization**: Role-based access control (admin, user, viewer)
- **授权**: 基于角色的访问控制（admin, user, viewer）
- **Audit Logging**: Complete audit trail of all actions
- **审计日志**: 所有操作的完整审计追踪
- **Content Filtering**: SQL injection, XSS, prompt injection protection
- **内容过滤**: SQL 注入、XSS、提示注入防护

### Supported Formats / 支持的格式:
- `.txt` - Plain text / 纯文本
- `.md` - Markdown documents / Markdown 文档
- `.pdf` - PDF documents / PDF 文档
- `.docx` - Microsoft Word / Microsoft Word 文档
- `.html` - HTML web pages / HTML 网页

### API Endpoints / API 端点:
#### Metrics / 指标 (Day 7):
- `GET /metrics` - Prometheus metrics / Prometheus 指标
- `GET /cache/stats` - Cache statistics / 缓存统计

#### Authentication / 认证 (Day 6):
- `POST /auth/register` - Register new user / 注册新用户
- `POST /auth/login` - Login and get token / 登录获取 token

#### Documents / 文档:
- `POST /documents/upload` - Upload document / 上传文档
- `GET /documents/list` - List documents / 列出文档

#### Chat / 聊天:
- `POST /chat/ask` - Ask question / 提问
""",
    version="7.0.0",
    lifespan=lifespan
)


# Day 7: Request timing middleware
# Day 7： 请求计时中间件
@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Add request timing to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Record metrics
    if settings.metrics_enabled:
        performance_service.record_request(
            method=request.method,
            path=request.url.path,
            duration=process_time,
            status_code=response.status_code
        )
    return response


# Add CORS middleware for frontend access
# 添加 CORS 中间件以供前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
                          # 在生产环境中，指定实际的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# 包含路由器
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(evaluation.router)
app.include_router(qa_history.router)
app.include_router(auth.router)
app.include_router(permissions.router)
app.include_router(audit.router)


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint returning API information
    返回 API 信息的根端点
    """
    return {
        "message": "Welcome to Step-by-Step RAG API - Day 7",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 7",
        "version": "7.0.0",
        "day": 7,
        "features": [
            "caching",
            "retry-logic",
            "metrics",
            "timeouts",
            "authentication",
            "authorization",
            "audit-logging",
            "content-filtering",
            "hybrid-search",
            "streaming",
            "citations",
            "evaluation",
        ],
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    健康检查端点
    """
    # Check database connection
    # 检查数据库连接
    db_status = "connected" if vector_store._vectorstore else "disconnected"

    # Day 3: Check BM25 index status
    # Day 3： 检查 BM25 索引状态
    bm25_indexed = retrieval_service._bm25_index._index is not None

    # Day 6: Get audit log count
    # Day 6： 获取审计日志计数
    audit_log_count = len(audit_service._logs)

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="7.0.0",
        day=7,
        bm25_indexed=bm25_indexed,
        streaming_enabled=True,
        evaluation_enabled=True,
        tracing_enabled=True
    )


# Day 7: Metrics endpoint
# Day 7： 指标端点
@app.get("/metrics")
async def get_metrics():
    """
    Get Prometheus-style metrics
    获取 Prometheus 风格的指标
    """
    if not settings.metrics_enabled:
        return {"error": "Metrics disabled"}

    return {
        "metrics": performance_service.get_metrics(),
        "cache_stats": {
            "enabled": settings.cache_enabled,
            "type": "redis" if settings.use_redis else "memory",
            "stats": cache_service.get_stats() if settings.cache_enabled else {}
        }
    }


# Day 7: Cache statistics endpoint
# Day 7： 缓存统计端点
@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics
    获取缓存统计
    """
    if not settings.cache_enabled:
        return {"error": "Cache disabled"}

    return cache_service.get_stats()


if __name__ == "__main__":
    import uvicorn
    # Run the application
    # 运行应用
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
