"""
Main entry point for the RAG API
RAG API 的主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import documents, chat
from services.vector_store import vector_store
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
## Day 1: Minimal RAG Implementation
## Day 1: 最小化 RAG 实现

A simple but complete RAG (Retrieval-Augmented Generation) system.
一个简单但完整的 RAG(检索增强生成)系统。

### Features / 功能:
- Upload text documents / 上传文本文档
- Automatic text chunking / 自动文本分块
- Vector storage with pgvector / 使用 pgvector 进行向量存储
- Question answering based on documents / 基于文档的问答
""",
    version="1.0.0",
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
        "message": "Welcome to Step-by-Step RAG API",
        "欢迎": "欢迎使用 Step-by-Step RAG API",
        "version": "1.0.0",
        "day": 1,
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
        version="1.0.0"
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
