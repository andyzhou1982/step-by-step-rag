"""
Main entry point for the RAG API
RAG API 的主入口

Day 8: LLM Wiki - Knowledge Compilation
Day 8： LLM Wiki - 知识编译

Adds Wiki page generation, storage, semantic search, and cross-referencing.
添加了 Wiki 页面生成、存储、语义搜索和交叉引用。
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat, evaluation, qa_history
from routers import auth, permissions, audit
from routers import wiki
from services.vector_store import vector_store
from services.retrieval_service import retrieval_service
from services.document_registry import document_registry
from services.qa_history_service import qa_history_service
from services.audit_service import audit_service
from services.auth_service import auth_service
from services.database_service import db_service
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

    # Connect to unified database service
    # 连接到统一的数据库服务
    await db_service.connect()

    # Create all tables if they don't exist (development only)
    # 创建所有不存在的表（仅开发环境）
    if settings.env == "development":
        logger.info("Creating database tables...")
        await db_service.create_tables()

    # Create default admin user if no users exist
    # 如果没有用户则创建默认管理员
    logger.info("Checking for default admin user...")
    await auth_service._create_default_admin()

    # Connect to vector store
    # 连接到向量存储
    await vector_store.connect()

    # Connect to QA history service
    # 连接到 QA 历史服务
    await qa_history_service.connect()

    logger.info("Databases connected.")

    # Day 3: Build BM25 index from existing documents
    # Day 3： 从现有文档构建 BM25 索引
    logger.info("Building BM25 index...")
    try:
        docs = await vector_store.get_all_documents_for_bm25()
        if docs:
            retrieval_service.build_bm25_index(docs)
            logger.info(f"BM25 index built with {len(docs)} documents.")
        else:
            logger.info("No documents found for BM25 index.")
    except Exception as e:
        logger.warning(f"Failed to build BM25 index: {e}", exc_info=True)

    yield

    # Shutdown: Disconnect from databases
    # 关闭: 断开数据库连接
    logger.info("Shutting down... Disconnecting from databases.")
    await vector_store.disconnect()
    await qa_history_service.disconnect()
    await db_service.disconnect()
    logger.info("Databases disconnected.")


# Create FastAPI application
# 创建 FastAPI 应用
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
## Day 8: LLM Wiki - Knowledge Compilation
## Day 8： LLM Wiki - 知识编译

Adds Wiki page generation, semantic search, and cross-referencing on top of the production RAG system.
在生产级 RAG 系统之上添加 Wiki 页面生成、语义搜索和交叉引用。

### Day 8 Features / Day 8 功能:
- **Wiki Generation**: LLM reads documents → extracts concepts → generates structured Wiki pages
- **Wiki 生成**: LLM 阅读文档 → 提取概念 → 生成结构化 Wiki 页面
- **Semantic Search**: Vector-based search across Wiki pages
- **语义搜索**: 基于 Wiki 页面的向量搜索
- **Cross-referencing**: Auto-linking Wiki pages by concept overlap
- **交叉引用**: 基于概念重叠自动链接 Wiki 页面

### Day 7 Features (Inherited) / Day 7 功能（继承）:
- **Production Ready**: Caching, retry, metrics, Docker
- **生产就绪**: 缓存、重试、指标、Docker

### Day 6 Features (Inherited) / Day 6 功能（继承）:
- **Authentication**: JWT-based user authentication
- **认证**: 基于 JWT 的用户认证
- **Authorization**: Role-based access control
- **授权**: 基于角色的访问控制
- **Audit Logging**: Complete audit trail
- **审计日志**: 完整审计追踪

### Wiki API Endpoints / Wiki API 端点:
- `POST /wiki/generate` - Generate Wiki pages from documents
- `POST /wiki/generate` - 从文档生成 Wiki 页面
- `GET /wiki/pages` - List all Wiki pages
- `GET /wiki/pages` - 列出所有 Wiki 页面
- `GET /wiki/pages/{id}` - Get Wiki page detail
- `GET /wiki/pages/{id}` - 获取 Wiki 页面详情
- `POST /wiki/search` - Semantic search Wiki pages
- `POST /wiki/search` - 语义搜索 Wiki 页面
- `GET /wiki/concepts` - List all concepts
- `GET /wiki/concepts` - 列出所有概念
- `GET /wiki/stats` - Wiki system statistics
- `GET /wiki/stats` - Wiki 系统统计
- `DELETE /wiki/pages/{id}` - Delete a Wiki page
- `DELETE /wiki/pages/{id}` - 删除 Wiki 页面
""",
    version="8.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend access
# 添加 CORS 中间件以供前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(wiki.router)


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint returning API information
    返回 API 信息的根端点
    """
    return {
        "message": "Welcome to Step-by-Step RAG API - Day 8",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 8",
        "version": "8.0.0",
        "day": 8,
        "features": [
            "wiki-generation",
            "wiki-semantic-search",
            "wiki-cross-referencing",
            "authentication",
            "authorization",
            "audit-logging",
            "content-filtering",
            "hybrid-search",
            "bm25",
            "query-rewrite",
            "rerank",
            "multi-format",
            "metadata",
            "smart-chunking",
            "streaming",
            "citations",
            "evaluation",
            "tracing"
        ],
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    """
    Health check endpoint
    健康检查端点
    """
    # Check actual connection liveness
    # 检查实际连接活性
    db_healthy = await db_service.health_check()
    vector_healthy = await vector_store.health_check()
    all_healthy = db_healthy and vector_healthy

    status = "healthy" if all_healthy else "unhealthy"
    db_status = "connected" if db_healthy else "disconnected"
    vector_status = "connected" if vector_healthy else "disconnected"

    # Day 3: Check BM25 index status (informational, not health-critical)
    # Day 3： 检查 BM25 索引状态（信息性，不影响健康状态）
    bm25_indexed = retrieval_service._bm25_index._index is not None

    # Day 6: Get audit log count safely
    # Day 6： 安全获取审计日志计数
    try:
        logs = await audit_service.get_logs(limit=1)
        audit_log_count = len(logs) if logs else 0
    except Exception:
        audit_log_count = 0

    if not all_healthy:
        response.status_code = 503

    return HealthResponse(
        status=status,
        db_status=db_status,
        vector_status=vector_status,
        version="8.0.0",
        day=8,
        bm25_indexed=bm25_indexed,
        streaming_enabled=True,
        evaluation_enabled=True,
        tracing_enabled=True
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
