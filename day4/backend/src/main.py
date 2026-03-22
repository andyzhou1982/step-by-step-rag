"""
Main entry point for the RAG API
RAG API 的主入口

Day 2: Enhanced with multi-format document support
Day 2： 增强了多格式文档支持

Day 3: Added hybrid retrieval with BM25 indexing
Day 3： 添加了带 BM25 索引的混合检索

Day 4: Added streaming, citations, and confidence scoring
Day 4： 添加了流式输出、引用溯源和置信度评分
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat
from services.vector_store import vector_store
from services.retrieval_service import retrieval_service
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
## Day 4: Generation Enhancement with Citations & Streaming
## Day 4: 引用溯源与流式输出的生成增强

A RAG (Retrieval-Augmented Generation) system with advanced generation features.
一个具有高级生成功能的 RAG（检索增强生成）系统。

### Day 4 Features / Day 4 功能:
- **Streaming responses**: Real-time answer generation via SSE
- **流式响应**: 通过 SSE 实时生成答案
- **Citation tracking**: Track which sources contribute to the answer
- **引用追踪**: 追踪哪些来源贡献了答案
- **Confidence scoring**: Evaluate answer reliability
- **置信度评分**: 评估答案可靠性
- **Anti-hallucination**: Strict context-based response generation
- **防幻觉**: 严格基于上下文的响应生成
- **Conversation management**: Enhanced history with metadata
- **对话管理**: 带元数据的增强历史

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
- `POST /documents/upload` - Upload document / 上传文档
- `GET /documents/list` - List documents / 列出文档
- `GET /documents/formats` - Supported formats / 支持的格式
- `DELETE /documents/{id}` - Delete document / 删除文档
- `POST /chat/ask` - Ask question (non-streaming) / 提问（非流式）
- `POST /chat/stream` - Ask question (streaming SSE) / 提问（流式 SSE）
- `GET /chat/conversations` - List conversations / 列出对话
- `GET /chat/conversations/{id}` - Get conversation history / 获取对话历史
- `GET /chat/retrieval-config` - Get retrieval config / 获取检索配置
""",
    version="4.0.0",
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


@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint returning API information
    返回 API 信息的根端点
    """
    return {
        "message": "Welcome to Step-by-Step RAG API - Day 4",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 4",
        "version": "4.0.0",
        "day": 4,
        "features": [
            "streaming",
            "citations",
            "confidence-scoring",
            "anti-hallucination",
            "conversation-management",
            "hybrid-search",
            "bm25",
            "query-rewrite",
            "rerank",
            "multi-format",
            "metadata",
            "smart-chunking"
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

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="4.0.0",
        day=4,
        bm25_indexed=bm25_indexed,
        streaming_enabled=settings.streaming_enabled,
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
