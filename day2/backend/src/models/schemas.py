"""
Data models and schemas for the RAG application
RAG 应用的数据模型和模式

Day 2 Enhancement: Added metadata support for documents
Day 2 增强： 添加了文档元数据支持
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ==================== Document Models ====================
# ==================== 文档模型 ====================

class DocumentMetadata(BaseModel):
    """
    Document metadata information
    文档元数据信息

    Day 2: Added to support document metadata extraction
    Day 2： 添加以支持文档元数据提取
    """
    # Document title (extracted from content)
    # 文档标题（从内容中提取）
    title: Optional[str] = None
    # File type (text, pdf, word, html, markdown)
    # 文件类型（text, pdf, word, html, markdown）
    file_type: str
    # File size in bytes
    # 文件大小（字节）
    file_size: int
    # Any additional metadata
    # 任何额外的元数据
    extra: Optional[Dict] = None


class DocumentUploadResponse(BaseModel):
    """
    Response after successful document upload
    文档上传成功后的响应

    Day 2: Added metadata field
    Day 2： 添加了元数据字段
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
    # Document metadata
    # 文档元数据
    metadata: Optional[DocumentMetadata] = None
    # File type
    # 文件类型
    file_type: str = "text"


class DocumentInfo(BaseModel):
    """
    Basic document information
    基本文档信息

    Day 2: Added metadata fields
    Day 2： 添加了元数据字段
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
    # File type
    # 文件类型
    file_type: str = "text"
    # File size in bytes
    # 文件大小（字节）
    file_size: int = 0
    # Document title
    # 文档标题
    title: Optional[str] = None


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
    # Supported file types
    # 支持的文件类型
    supported_types: List[str] = ["txt", "pdf", "docx", "html", "md"]


class SupportedFormatsResponse(BaseModel):
    """
    Response listing supported file formats
    列出支持的文件格式的响应

    Day 2: New endpoint to show supported formats
    Day 2： 新端点显示支持的格式
    """
    # Supported file extensions
    # 支持的文件扩展名
    extensions: List[str]
    # Format descriptions
    # 格式描述
    descriptions: Dict[str, str]


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
    # Optional file type filter for search
    # 可选的文件类型过滤器用于搜索
    file_types: Optional[List[str]] = None


class SourceReference(BaseModel):
    """
    Reference to source document
    源文档引用

    Day 2: Added file_type field
    Day 2： 添加了 file_type 字段
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
    # File type
    # 文件类型
    file_type: str = "text"


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
    version: str = "2.0.0"
    # Day number
    # 天数
    day: int = 2
