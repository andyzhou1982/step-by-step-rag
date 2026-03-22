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
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
from models.schemas import HealthResponse
from config import settings


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
        documents = await vector_store.get_all_documents_for_bm25()
        if documents:
            retrieval_service.build_bm25_index(documents)
            print(f"BM25 index built with {len(documents)} documents.")
            print(f"BM25 索引已构建，包含 {len(documents)} 个文档。")
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

    yield

    # Shutdown: Disconnect from database
    # 关闭: 断开数据库连接
    print("Shutting down... Disconnecting from database.")
    print("正在关闭... 断开数据库连接。")
    await vector_store.disconnect()
    print("Database disconnected.")
    print("数据库已断开。")


# Create FastAPI application
# 创建 FastAPI 应用
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
## Day 6: Security & Governance
## Day 6: 安全与治理

A RAG (Retrieval-Augmented Generation) system with enterprise-grade security.
一个具有企业级安全功能的 RAG（检索增强生成）系统。

### Day 6 Features / Day 6 功能:
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
- **PII Detection**: Automatic detection and masking of sensitive data
- **PII 检测**: 自动检测和遮罩敏感数据

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

### Authentication Endpoints / 认证端点:
- `POST /auth/register` - Register new user / 注册新用户
- `POST /auth/login` - Login and get JWT token / 登录并获取 JWT token
- `POST /auth/logout` - Logout / 登出
- `GET /auth/me` - Get current user info / 获取当前用户信息
- `GET /auth/users` - List users (admin) / 列出用户（管理员）

### Permission Endpoints / 权限端点:
- `POST /permissions/grant` - Grant permission / 授予权限
- `DELETE /permissions/revoke/{doc}/{user}` - Revoke permission / 撤销权限
- `GET /permissions/document/{id}` - Get document permissions / 获取文档权限
- `GET /permissions/check/{doc}` - Check user permission / 检查用户权限

### Audit Endpoints / 审计端点:
- `GET /audit/logs` - Get audit logs (admin) / 获取审计日志（管理员）
- `GET /audit/summary` - System activity summary / 系统活动摘要
- `GET /audit/my-activity` - User's own activity / 用户自身活动
- `GET /audit/export` - Export audit logs / 导出审计日志
""",
    version="6.0.0",
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


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint returning API information
    返回 API 信息的根端点
    """
    return {
        "message": "Welcome to Step-by-Step RAG API - Day 6",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 6",
        "version": "6.0.0",
        "day": 6,
        "features": [
            "jwt-authentication",
            "role-based-access",
            "document-permissions",
            "audit-logging",
            "content-filtering",
            "pii-detection",
            "ragas-evaluation",
            "retrieval-metrics",
            "request-tracing",
            "streaming",
            "citations",
            "confidence-scoring",
            "hybrid-search",
            "bm25",
            "multi-format",
        ],
        "docs": "/docs",
        "default_credentials": {
            "username": "admin",
            "password": "admin123",
            "note": "Change in production!"
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
        version="6.0.0",
        day=6,
        bm25_indexed=bm25_indexed,
        streaming_enabled=settings.streaming_enabled,
        evaluation_enabled=settings.evaluation_enabled,
        tracing_enabled=settings.tracing_enabled,
        auth_enabled=settings.auth_enabled,
        audit_enabled=settings.audit_enabled,
        content_filter_enabled=settings.content_filter_enabled,
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
