"""
Main entry point for the RAG API
RAG API 的主入口

Day 2: Enhanced with multi-format document support
Day 2： 增强了多格式文档支持

Day 3: Added hybrid retrieval with BM25 indexing
Day 3： 添加了带 BM25 索引的混合检索

Day 4: Added streaming, citations, and confidence scoring
Day 4： 添加了流式输出、引用溯源和置信度评分

Day 5: Added evaluation and tracing
Day 5： 添加了评估和追踪

Day 6: Added authentication, permissions, audit, and content filtering
Day 6： 添加了认证、权限、审计和内容过滤

Day 7: Production optimization - caching, retry, metrics, rate limiting
Day 7： 生产优化 - 缓存、重试、指标、速率限制
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from typing import Callable

from routers import documents, chat, evaluation
from routers import auth, permissions, audit
from services.vector_store import vector_store
from services.retrieval_service import retrieval_service
from services.evaluation_service import evaluation_service
from services.tracing_service import tracing_service
from services.auth_service import auth_service
from services.permission_service import permission_service
from services.audit_service import audit_service
from services.content_filter_service import content_filter_service
from services.cache_service import cache_service
from services.performance_service import performance_metrics
from models.schemas import HealthResponse
from config import settings


# Middleware for request timing and metrics
# 请求计时和指标中间件
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to track request timing and performance metrics
    跟踪请求计时和性能指标的中间件
    """
    start_time = time.time()

    # Process the request
    # 处理请求
    response = await call_next(request)

    # Calculate latency
    # 计算延迟
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics
    # 记录指标
    operation = f"{request.method} {request.url.path}"
    performance_metrics.record_latency(operation, latency_ms)
    performance_metrics.record_request(
        operation,
        success=200 <= response.status_code < 400
    )

    # Add timing header
    # 添加计时头部
    response.headers["X-Process-Time-Ms"] = f"{latency_ms:.2f}"

    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown
    应用生命周期管理器，用于启动和关闭
    """
    # Startup: Connect to database
    # 启动: 连接数据库
    print("Starting up... Connecting to database.")
    print("正在启动... 连接数据库。")
    await vector_store.connect()
    print("Database connected.")
    print("数据库已连接。")

    # Day 3: Build BM25 index from existing documents
    # Day 3： 从现有文档构建 BM25 索引
    print("Building BM25 index...")
    print("正在构建 BM25 索引...")
    try:
        documents_list = await vector_store.get_all_documents_for_bm25()
        if documents_list:
            retrieval_service.build_bm25_index(documents_list)
            print(f"BM25 index built with {len(documents_list)} documents.")
            print(f"BM25 索引已构建，包含 {len(documents_list)} 个文档。")
        else:
            print("No documents found for BM25 index.")
            print("未找到用于 BM25 索引的文档。")
    except Exception as e:
        print(f"Warning: Failed to build BM25 index: {e}")
        print(f"警告：构建 BM25 索引失败：{e}")

    # Day 6: Print security status
    # Day 6： 打印安全状态
    print("\n=== Security Status / 安全状态 ===")
    print(f"Authentication: {'Enabled' if settings.auth_enabled else 'Disabled'}")
    print(f"认证: {'已启用' if settings.auth_enabled else '已禁用'}")
    print(f"Audit logging: {'Enabled' if settings.audit_enabled else 'Disabled'}")
    print(f"审计日志: {'已启用' if settings.audit_enabled else '已禁用'}")
    print(f"Content filtering: {'Enabled' if settings.content_filter_enabled else 'Disabled'}")
    print(f"内容过滤: {'已启用' if settings.content_filter_enabled else '已禁用'}")
    print(f"Default admin user: admin / admin123")
    print(f"默认管理员用户: admin / admin123")
    print("================================\n")

    # Day 7: Print production status
    # Day 7： 打印生产状态
    print("=== Production Status / 生产状态 ===")
    print(f"Caching: {'Enabled' if settings.cache_enabled else 'Disabled'}")
    print(f"缓存: {'已启用' if settings.cache_enabled else '已禁用'}")
    print(f"Metrics: {'Enabled' if settings.metrics_enabled else 'Disabled'}")
    print(f"指标: {'已启用' if settings.metrics_enabled else '已禁用'}")
    print(f"Rate limiting: {'Enabled' if settings.rate_limit_enabled else 'Disabled'}")
    print(f"速率限制: {'已启用' if settings.rate_limit_enabled else '已禁用'}")
    print(f"Retry logic: Enabled (max {settings.retry_max_attempts} attempts)")
    print(f"重试逻辑: 已启用 (最大 {settings.retry_max_attempts} 次)")
    print("==================================\n")

    yield

    # Shutdown: Disconnect from database
    # 关闭: 断开数据库连接
    print("Shutting down... Disconnecting from database.")
    print("正在关闭... 断开数据库连接。")
    await vector_store.disconnect()

    # Day 7: Clear cache on shutdown
    # Day 7： 关闭时清除缓存
    if settings.cache_enabled:
        await cache_service.clear()
        print("Cache cleared.")
        print("缓存已清除。")

    print("Database disconnected.")
    print("数据库已断开。")


# Create FastAPI application
# 创建 FastAPI 应用
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
## Day 7: Production Ready
## Day 7: 生产就绪

A fully-featured RAG (Retrieval-Augmented Generation) system ready for production deployment.
一个功能完整、可投入生产的 RAG（检索增强生成）系统。

### Day 7 Features / Day 7 功能:
- **Caching**: In-memory and Redis caching for query results
- **缓存**: 查询结果的内存和 Redis 缓存
- **Performance Metrics**: Latency tracking and throughput monitoring
- **性能指标**: 延迟跟踪和吞吐量监控
- **Retry Logic**: Automatic retry with exponential backoff
- **重试逻辑**: 带有指数退避的自动重试
- **Rate Limiting**: Request rate limiting for API protection
- **速率限制**: API 保护的请求速率限制
- **Docker Ready**: Complete Docker deployment configuration
- **Docker 就绪**: 完整的 Docker 部署配置

### Day 6 Features (Inherited) / Day 6 功能（继承）:
- **JWT Authentication**: Secure user authentication with JWT tokens
- **JWT 认证**: 使用 JWT token 的安全用户认证
- **Role-based Access Control**: Admin, User, Viewer roles
- **基于角色的访问控制**: 管理员、用户、查看者角色
- **Document-level Permissions**: Fine-grained ACL control
- **文档级权限**: 细粒度的 ACL 控制
- **Audit Logging**: Comprehensive action tracking
- **审计日志**: 全面的操作追踪
- **Content Filtering**: SQL injection, XSS, prompt injection detection
- **内容过滤**: SQL 注入、XSS、提示注入检测

### Day 5 Features (Inherited) / Day 5 功能（继承）:
- **RAGAS evaluation**: Faithfulness, Answer Relevance, Context Precision/Recall
- **RAGAS 评估**: 忠实度、答案相关性、上下文精确度/召回率
- **Retrieval metrics**: Recall@K, Precision@K, MRR, NDCG
- **检索指标**: Recall@K, Precision@K, MRR, NDCG
- **Request tracing**: OpenTelemetry-based distributed tracing
- **请求追踪**: 基于 OpenTelemetry 的分布式追踪

### Day 4 Features (Inherited) / Day 4 功能（继承）:
- **Streaming responses**: Real-time answer generation via SSE
- **流式响应**: 通过 SSE 实时生成答案
- **Citation tracking**: Track which sources contribute to the answer
- **引用追踪**: 追踪哪些来源贡献了答案
- **Confidence scoring**: Evaluate answer reliability
- **置信度评分**: 评估答案可靠性

### Day 3 Features (Inherited) / Day 3 功能（继承）:
- **Hybrid search**: Vector + BM25 keyword search
- **混合检索**: 向量 + BM25 关键词搜索
- **Query rewriting**: Optional LLM-based query optimization
- **查询重写**: 可选的基于 LLM 的查询优化
- **Re-ranking**: Cross-encoder result re-ranking
- **重排序**: 交叉编码器结果重排序

### Supported Formats / 支持的格式:
- `.txt` - Plain text / 纯文本
- `.md` - Markdown documents / Markdown 文档
- `.pdf` - PDF documents / PDF 文档
- `.docx` - Microsoft Word / Microsoft Word 文档
- `.html` - HTML web pages / HTML 网页

### Production Endpoints / 生产端点:
- `GET /metrics` - Get performance metrics / 获取性能指标
- `GET /health` - Detailed health check / 详细健康检查
- `GET /cache/stats` - Cache statistics / 缓存统计

### Authentication Endpoints / 认证端点:
- `POST /auth/register` - Register new user / 注册新用户
- `POST /auth/login` - Login and get JWT token / 登录并获取 JWT token
- `POST /auth/logout` - Logout / 登出
- `GET /auth/me` - Get current user info / 获取当前用户信息

### Permission Endpoints / 权限端点:
- `POST /permissions/grant` - Grant permission / 授予权限
- `DELETE /permissions/revoke/{doc}/{user}` - Revoke permission / 撤销权限
- `GET /permissions/document/{id}` - Get document permissions / 获取文档权限

### Audit Endpoints / 审计端点:
- `GET /audit/logs` - Get audit logs (admin) / 获取审计日志（管理员）
- `GET /audit/summary` - System activity summary / 系统活动摘要
- `GET /audit/export` - Export audit logs / 导出审计日志
""",
    version="7.0.0",
    lifespan=lifespan
)

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
app.include_router(auth.router)
app.include_router(permissions.router)
app.include_router(audit.router)


@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for request timing and metrics
    请求计时和指标中间件
    """
    return await metrics_middleware(request, call_next)


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint returning API information
    返回 API 信息的根端点
    """
    return {
        "message": "Welcome to Step-by-Step RAG API - Day 7 (Production Ready)",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 7（生产就绪）",
        "version": "7.0.0",
        "day": 7,
        "features": [
            # Day 7
            "caching",
            "performance-metrics",
            "retry-logic",
            "rate-limiting",
            "docker-ready",
            # Day 6
            "jwt-authentication",
            "role-based-access",
            "document-permissions",
            "audit-logging",
            "content-filtering",
            "pii-detection",
            # Day 5
            "ragas-evaluation",
            "retrieval-metrics",
            "request-tracing",
            # Day 4
            "streaming",
            "citations",
            "confidence-scoring",
            # Day 3
            "hybrid-search",
            "bm25",
            "query-rewrite",
            "rerank",
            # Day 2
            "multi-format",
            # Day 1
            "vector-search",
            "document-upload",
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "metrics": "/metrics",
        "health": "/health",
        "default_credentials": {
            "username": "admin",
            "password": "admin123",
            "note": "Change in production! / 在生产环境中更改！"
        }
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

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="7.0.0",
        day=7,
        bm25_indexed=bm25_indexed,
        streaming_enabled=settings.streaming_enabled,
        evaluation_enabled=settings.evaluation_enabled,
        tracing_enabled=settings.tracing_enabled,
        auth_enabled=settings.auth_enabled,
        audit_enabled=settings.audit_enabled,
        content_filter_enabled=settings.content_filter_enabled,
    )


# Day 7: Performance metrics endpoint
# Day 7： 性能指标端点
@app.get("/metrics")
async def get_metrics():
    """
    Get performance metrics
    获取性能指标

    Returns latency, throughput, and error rate statistics
    返回延迟、吞吐量和错误率统计
    """
    return performance_metrics.get_all_metrics()


# Day 7: Cache statistics endpoint
# Day 7： 缓存统计端点
@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics
    获取缓存统计

    Returns cache hit rate, size, and configuration
    返回缓存命中率、大小和配置
    """
    return await cache_service.get_stats()


if __name__ == "__main__":
    import uvicorn
    # Run the application
    # 运行应用
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
