"""
Main entry point for the RAG API
RAG API 的主入口

Day 2: Enhanced with multi-format document support
Day 2： 增强了多格式文档支持

Day 3: Added hybrid retrieval with BM25 indexing
Day 3： 添加了带 BM25 索引的混合检索

Day 7: Production Ready - Performance, Deployment, Monitoring
Day 7： 生产就绪 - 性能、部署、监控

Day 6: Security & Governance - Authentication, Authorization, Audit
Day 6： 安全与治理 - 认证、授权、审计
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat, evaluation, qa_history
from routers import auth, permissions, audit
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

    # Create all tables if they don't exist
    # 创建所有不存在的表
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
        documents = await vector_store.get_all_documents_for_bm25()
        if documents:
            retrieval_service.build_bm25_index(documents)
            logger.info(f"BM25 index built with {len(documents)} documents.")
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
## Day 7: Production Ready
## Day 7: 生产就绪

A production-ready RAG system with performance optimization and monitoring capabilities.
一个具有性能优化和监控功能的生产就绪 RAG 系统。

### Day 7 Features / Day 7 功能:
- **Unified Database**: All data stored in PostgreSQL using SQLAlchemy ORM
- **统一数据库**: 所有数据使用 SQLAlchemy ORM 存储在 PostgreSQL
- **Performance**: Caching, retry logic, connection pooling
- **性能**: 缓存、重试逻辑、连接池
- **Monitoring**: Performance metrics and health checks
- **监控**: 性能指标和健康检查

### Day 6 Features (Inherited) / Day 6 功能（继承）:
- **Authentication**: JWT-based user authentication
- **认证**: 基于 JWT 的用户认证
- **Authorization**: Role-based access control (admin, user, viewer)
- **授权**: 基于角色的访问控制（admin, user, viewer）
- **Audit Logging**: Complete audit trail of all actions
- **审计日志**: 所有操作的完整审计追踪
- **Content Filtering**: SQL injection, XSS, prompt injection protection
- **内容过滤**: SQL 注入、XSS、提示注入防护

### Day 3 Features (Inherited) / Day 3 功能（继承）:
- **Hybrid search**: Vector + BM25 keyword search
- **混合检索**: 向量 + BM25 关键词搜索
- **Query rewriting**: Optional LLM-based query optimization
- **查询重写**: 可选的基于 LLM 的查询优化
- **Re-ranking**: Cross-encoder result re-ranking
- **重排序**: 交叉编码器结果重排序

### Day 2 Features (Inherited) / Day 2 功能（继承）:
- **Multi-format support**: PDF, Word, HTML, Markdown, TXT
- **多格式支持**: PDF, Word, HTML, Markdown, TXT
- **Metadata extraction**: Title, file type, size
- **元数据提取**: 标题、文件类型、大小
- **Smart chunking**: Format-aware text splitting
- **智能分块**: 格式感知的文本分割

### Supported Formats / 支持的格式:
- `.txt` - Plain text / 纯文本
- `.md` - Markdown documents / Markdown 文档
- `.pdf` - PDF documents / PDF 文档
- `.docx` - Microsoft Word / Microsoft Word 文档
- `.html` - HTML web pages / HTML 网页

### API Endpoints / API 端点:
#### Authentication / 认证:
- `POST /auth/register` - Register new user / 注册新用户
- `POST /auth/login` - Login and get token / 登录获取 token
- `POST /auth/logout` - Logout / 登出
- `GET /auth/me` - Get current user info / 获取当前用户信息
- `GET /auth/users` - List all users (admin) / 列出所有用户（管理员）
- `PUT /auth/users/{id}/role` - Update user role (admin) / 更新用户角色（管理员）

#### Documents / 文档:
- `POST /documents/upload` - Upload document / 上传文档
- `GET /documents/list` - List documents / 列出文档
- `DELETE /documents/{id}` - Delete document / 删除文档

#### Chat / 聊天:
- `POST /chat/ask` - Ask question / 提问
- `GET /chat/retrieval-config` - Get retrieval config / 获取检索配置

#### Audit / 审计:
- `GET /audit/logs` - Get audit logs (admin) / 获取审计日志（管理员）
- `GET /audit/summary` - Get audit summary (admin) / 获取审计摘要（管理员）
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

    # Day 6: Get audit log count from database
    # Day 6： 从数据库获取审计日志计数
    logs = await audit_service.get_logs(limit=1)
    audit_log_count = len(logs) if logs else 0  # Just check if logs exist

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="7.0.0",
        day=6,
        bm25_indexed=bm25_indexed,
        streaming_enabled=True,
        evaluation_enabled=True,
        tracing_enabled=True
    )


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
