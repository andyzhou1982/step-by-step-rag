"""
Data models and schemas for the RAG application
RAG 应用的数据模型和模式
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ==================== Document Models ====================
# ==================== 文档模型 ====================

class DocumentUploadResponse(BaseModel):
    """
    Response after successful document upload
    文档上传成功后的响应
    """
    # Document ID assigned by the system
    # 系统分配的文档 ID
    document_id: str
    # Original filename
    # 原始文件名
    filename: str
    # Number of chunks created
    # 创建的分块数量
    chunk_count: int
    # Upload timestamp
    # 上传时间戳
    created_at: datetime


class DocumentInfo(BaseModel):
    """
    Basic document information
    基本文档信息
    """
    # Document ID
    # 文档 ID
    id: str
    # Original filename
    # 原始文件名
    filename: str
    # Number of chunks
    # 分块数量
    chunk_count: int
    # Creation timestamp
    # 创建时间戳
    created_at: datetime


class DocumentListResponse(BaseModel):
    """
    Response containing list of documents
    包含文档列表的响应
    """
    # List of documents
    # 文档列表
    documents: List[DocumentInfo]
    # Total count
    # 总数
    total: int


# ==================== Chat Models ====================
# ==================== 聊天模型 ====================

class ChatRequest(BaseModel):
    """
    User's chat request
    用户的聊天请求
    """
    # User's question
    # 用户的问题
    question: str
    # Optional conversation ID for context
    # 可选的对话 ID 用于上下文
    conversation_id: Optional[str] = None


class SourceReference(BaseModel):
    """
    Reference to source document
    源文档引用
    """
    # Document ID
    # 文档 ID
    document_id: str
    # Original filename
    # 原始文件名
    filename: str
    # Relevant text chunk
    # 相关文本分块
    content: str
    # Similarity score
    # 相似度分数
    score: float


class ChatResponse(BaseModel):
    """
    AI's response to user's question
    AI 对用户问题的回答
    """
    # The generated answer
    # 生成的回答
    answer: str
    # Source documents used
    # 使用的源文档
    sources: List[SourceReference]
    # Conversation ID for follow-up
    # 后续对话的对话 ID
    conversation_id: str


# ==================== Common Models ====================
# ==================== 通用模型 ====================

class ApiResponse(BaseModel):
    """
    Standard API response wrapper
    标准 API 响应包装器
    """
    # Whether the request was successful
    # 请求是否成功
    success: bool
    # Response data
    # 响应数据
    data: Optional[dict] = None
    # Error message if any
    # 错误信息（如果有）
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """
    Health check response
    健康检查响应
    """
    # Service status
    # 服务状态
    status: str
    # Database connection status
    # 数据库连接状态
    database: str
    # API version
    # API 版本
    version: str = "1.0.0"
