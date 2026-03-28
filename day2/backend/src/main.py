"""
Main entry point for the RAG API
RAG API 的主入口

Day 2: Enhanced with multi-format document support
Day 2： 增强了多格式文档支持
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat
from services.vector_store import vector_store
from services.document_registry import document_registry
from models.schemas import HealthResponse
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown
    应用生命周期管理器，用于启动和关闭
    """
    # Startup: Connect to databases
    # 启动: 连接数据库
    print("Starting up... Connecting to databases.")
    print("正在启动... 连接数据库。")
    await vector_store.connect()
    await document_registry.connect()
    print("Databases connected.")
    print("数据库已连接。")

    yield

    # Shutdown: Disconnect from databases
    # 关闭: 断开数据库连接
    print("Shutting down... Disconnecting from databases.")
    print("正在关闭... 断开数据库连接。")
    await vector_store.disconnect()
    await document_registry.disconnect()
    print("Databases disconnected.")
    print("数据库已断开。")


# Create FastAPI application
# 创建 FastAPI 应用
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
## Day 2: Enhanced Document Processing
## Day 2: 增强的文档处理

A RAG (Retrieval-Augmented Generation) system with multi-format document support.
一个支持多格式文档的 RAG（检索增强生成）系统。

### Day 2 Features / Day 2 功能:
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
- `POST /chat/ask` - Ask question / 提问
""",
    version="2.0.0",
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
        "message": "Welcome to Step-by-Step RAG API - Day 2",
        "欢迎": "欢迎使用 Step-by-Step RAG API - Day 2",
        "version": "2.0.0",
        "day": 2,
        "features": ["multi-format", "metadata", "smart-chunking"],
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

    return HealthResponse(
        status="healthy",
        database=db_status,
        version="2.0.0",
        day=2
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
