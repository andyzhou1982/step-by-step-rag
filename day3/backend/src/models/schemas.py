"""
Data models and schemas for the RAG application
RAG 应用的数据模型和模式

Day 2 Enhancement: Added metadata support for documents
Day 2 增强： 添加了文档元数据支持

Day 3 Enhancement: Added retrieval configuration and source tracking
Day 3 增强： 添加了检索配置和来源追踪
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
    title: Optional[str] = None
    file_type: str
    file_size: int
    extra: Optional[Dict] = None


class DocumentUploadResponse(BaseModel):
    """
    Response after successful document upload
    文档上传成功后的响应
    """
    document_id: str
    filename: str
    chunk_count: int
    created_at: datetime
    metadata: Optional[DocumentMetadata] = None
    file_type: str = "text"


class DocumentInfo(BaseModel):
    """
    Basic document information
    基本文档信息
    """
    id: str
    filename: str
    chunk_count: int
    created_at: datetime
    file_type: str = "text"
    file_size: int = 0
    title: Optional[str] = None


class DocumentListResponse(BaseModel):
    """
    Response containing list of documents
    包含文档列表的响应
    """
    documents: List[DocumentInfo]
    total: int
    supported_types: List[str] = ["txt", "pdf", "docx", "html", "md"]


class SupportedFormatsResponse(BaseModel):
    """
    Response listing supported file formats
    列出支持的文件格式的响应
    """
    extensions: List[str]
    descriptions: Dict[str, str]


# ==================== Retrieval Configuration (Day 3) ====================
# ==================== 检索配置（Day 3）====================

class RetrievalConfig(BaseModel):
    """
    Retrieval configuration options
    检索配置选项

    Day 3: Added for retrieval customization
    Day 3： 添加用于检索自定义
    """
    # Whether to use hybrid search (vector + BM25)
    # 是否使用混合检索（向量 + BM25）
    use_hybrid: bool = True
    # Whether to rewrite the query
    # 是否重写查询
    use_rewrite: bool = False
    # Whether to re-rank results
    # 是否重排序结果
    use_rerank: bool = True
    # Number of results to retrieve
    # 检索的结果数量
    top_k: int = 5
    # Weight for vector search (0-1)
    # 向量搜索权重（0-1）
    vector_weight: float = 0.6
    # Weight for BM25 search (0-1)
    # BM25 搜索权重（0-1）
    bm25_weight: float = 0.4


class RetrievalConfigResponse(BaseModel):
    """
    Response with current retrieval configuration
    当前检索配置的响应

    Day 3: New endpoint to show retrieval settings
    Day 3： 新端点显示检索设置
    """
    config: RetrievalConfig
    available_strategies: List[str] = ["vector", "bm25", "hybrid"]
    features: List[str] = ["query_rewrite", "rerank"]


# ==================== Chat Models ====================
# ==================== 聊天模型 ====================

class ChatRequest(BaseModel):
    """
    User's chat request
    用户的聊天请求

    Day 3: Added retrieval configuration options
    Day 3： 添加了检索配置选项
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
    # Retrieval configuration (Day 3)
    # 检索配置（Day 3）
    retrieval_config: Optional[RetrievalConfig] = None


class SourceReference(BaseModel):
    """
    Reference to source document
    源文档引用

    Day 3: Added source field to track retrieval method
    Day 3： 添加了 source 字段追踪检索方法
    """
    document_id: str
    filename: str
    content: str
    score: float
    file_type: str = "text"
    # Source of the result: "vector", "bm25", "hybrid", or "reranked"
    # 结果来源："vector", "bm25", "hybrid", 或 "reranked"
    source: str = "hybrid"


class ChatResponse(BaseModel):
    """
    AI's response to user's question
    AI 对用户问题的回答

    Day 3: Added retrieval info
    Day 3： 添加了检索信息
    """
    answer: str
    sources: List[SourceReference]
    conversation_id: str
    # Retrieval method used
    # 使用的检索方法
    retrieval_method: str = "hybrid"
    # Whether query was rewritten
    # 查询是否被重写
    query_rewritten: bool = False
    # Original query if rewritten
    # 如果重写后的原始查询
    original_query: Optional[str] = None


# ==================== Common Models ====================
# ==================== 通用模型 ====================

class ApiResponse(BaseModel):
    """
    Standard API response wrapper
    标准 API 响应包装器
    """
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """
    Health check response
    健康检查响应
    """
    status: str
    db_status: str
    vector_status: str
    version: str = "3.0.0"
    day: int = 3
    # Day 3: BM25 index status
    # Day 3： BM25 索引状态
    bm25_indexed: bool = False
