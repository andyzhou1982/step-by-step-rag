"""
Data models and schemas for the RAG application
RAG 应用的数据模型和模式

Day 2 Enhancement: Added metadata support for documents
Day 2 增强： 添加了文档元数据支持

Day 3 Enhancement: Added retrieval configuration and source tracking
Day 3 增强： 添加了检索配置和来源追踪

Day 4 Enhancement: Added citation, streaming, and confidence scoring
Day 4 增强： 添加了引用溯源、流式输出和置信度评分

Day 5 Enhancement: Added evaluation and tracing models
Day 5 增强： 添加了评估和追踪模型
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

    Day 4: Added streaming feature
    Day 4： 添加了流式功能
    """
    config: RetrievalConfig
    available_strategies: List[str] = ["vector", "bm25", "hybrid"]
    features: List[str] = ["query_rewrite", "rerank", "streaming", "citations"]


# ==================== Chat Models ====================
# ==================== 聊天模型 ====================

class ChatRequest(BaseModel):
    """
    User's chat request
    用户的聊天请求

    Day 3: Added retrieval configuration options
    Day 3： 添加了检索配置选项

    Day 4: Added streaming option
    Day 4： 添加了流式选项
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
    # Day 4: Whether to stream the response
    # Day 4： 是否流式传输响应
    stream: bool = False
    # Day 4: Maximum context length (in tokens)
    # Day 4： 最大上下文长度（以 token 计）
    max_context_tokens: int = 3000


class SourceReference(BaseModel):
    """
    Reference to source document
    源文档引用

    Day 3: Added source field to track retrieval method
    Day 3： 添加了 source 字段追踪检索方法

    Day 4: Added citation_id for citation tracking
    Day 4： 添加了 citation_id 用于引用追踪
    """
    document_id: str
    filename: str
    content: str
    score: float
    file_type: str = "text"
    # Source of the result: "vector", "bm25", "hybrid", or "reranked"
    # 结果来源："vector", "bm25", "hybrid", 或 "reranked"
    source: str = "hybrid"
    # Day 4: Citation ID for reference in answer (e.g., [1], [2])
    # Day 4： 答案中引用的 ID（如 [1], [2]）
    citation_id: int = 0


class ChatResponse(BaseModel):
    """
    AI's response to user's question
    AI 对用户问题的回答

    Day 3: Added retrieval info
    Day 3： 添加了检索信息

    Day 4: Added confidence score and context utilization
    Day 4： 添加了置信度评分和上下文利用率
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
    # Day 4: Confidence score (0-1) based on context relevance
    # Day 4： 基于上下文相关性的置信度评分（0-1）
    confidence: float = 0.0
    # Day 4: Whether the answer is based on provided context
    # Day 4： 答案是否基于提供的上下文
    is_context_based: bool = True
    # Day 4: Number of tokens in context used
    # Day 4： 使用的上下文 token 数量
    context_tokens: int = 0


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
    database: str
    version: str = "5.0.0"
    day: int = 5
    # Day 3: BM25 index status
    # Day 3： BM25 索引状态
    bm25_indexed: bool = False
    # Day 4: Streaming support
    # Day 4： 流式支持
    streaming_enabled: bool = True
    # Day 5: Evaluation and tracing support
    # Day 5： 评估和追踪支持
    evaluation_enabled: bool = True
    tracing_enabled: bool = True


# ==================== Streaming Models (Day 4) ====================
# ==================== 流式模型（Day 4）====================

class StreamChunk(BaseModel):
    """
    A single chunk of streaming response
    流式响应的单个分块

    Day 4: New model for SSE streaming
    Day 4： SSE 流式传输的新模型
    """
    # Type of chunk: "content", "sources", "done", "error"
    # 分块类型："content", "sources", "done", "error"
    type: str
    # Content of the chunk
    # 分块内容
    content: Optional[str] = None
    # Sources (only in "sources" type)
    # 来源（仅在 "sources" 类型中）
    sources: Optional[List[SourceReference]] = None
    # Conversation ID
    # 对话 ID
    conversation_id: Optional[str] = None
    # Confidence score (only in "done" type)
    # 置信度评分（仅在 "done" 类型中）
    confidence: Optional[float] = None
    # Error message (only in "error" type)
    # 错误消息（仅在 "error" 类型中）
    error: Optional[str] = None


# ==================== Conversation Models (Day 4) ====================
# ==================== 对话模型（Day 4）====================

class ConversationMessage(BaseModel):
    """
    A single message in conversation history
    对话历史中的单条消息

    Day 4: New model for conversation management
    Day 4： 对话管理的新模型
    """
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    # Sources used in this message (for assistant messages)
    # 此消息中使用的来源（用于助手消息）
    sources: Optional[List[SourceReference]] = None


class ConversationHistory(BaseModel):
    """
    Conversation history response
    对话历史响应

    Day 4: New model for conversation history endpoint
    Day 4： 对话历史端点的新模型
    """
    conversation_id: str
    messages: List[ConversationMessage]
    message_count: int
    created_at: datetime
    last_updated: datetime


class ConversationSummary(BaseModel):
    """
    Summary of a conversation
    对话摘要

    Day 4: New model for conversation list
    Day 4： 对话列表的新模型
    """
    conversation_id: str
    preview: str  # First 100 chars of last message
    message_count: int
    created_at: datetime
    last_updated: datetime


# ==================== Evaluation Models (Day 5) ====================
# ==================== 评估模型（Day 5）====================

class EvaluationMetrics(BaseModel):
    """
    RAGAS evaluation metrics
    RAGAS 评估指标

    Day 5: New model for evaluation results
    Day 5： 评估结果的新模型
    """
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    overall_score: float = 0.0


class RetrievalMetrics(BaseModel):
    """
    Retrieval quality metrics
    检索质量指标

    Day 5: New model for retrieval evaluation
    Day 5： 检索评估的新模型
    """
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg_at_k: float = 0.0  # Normalized Discounted Cumulative Gain


class EvaluationRequest(BaseModel):
    """
    Request to evaluate a RAG query-response pair
    评估 RAG 查询-响应对的请求

    Day 5: New model for evaluation endpoint
    Day 5： 评估端点的新模型
    """
    question: str
    answer: str
    contexts: List[str]
    # Ground truth for context_recall (optional)
    # 用于 context_recall 的真实答案（可选）
    ground_truth: Optional[str] = None


class RetrievalEvaluationRequest(BaseModel):
    """
    Request to evaluate retrieval quality
    评估检索质量的请求

    Day 5: New model for retrieval evaluation endpoint
    Day 5： 检索评估端点的新模型
    """
    query: str
    retrieved_ids: List[str]
    relevant_ids: List[str]
    k: int = 5


class EvaluationResponse(BaseModel):
    """
    Response containing evaluation results
    包含评估结果的响应

    Day 5: New model for evaluation response
    Day 5： 评估响应的新模型
    """
    rag_metrics: EvaluationMetrics
    retrieval_metrics: Optional[RetrievalMetrics] = None
    evaluation_time_ms: float = 0.0
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "rag_metrics": {
                    "faithfulness": 0.85,
                    "answer_relevance": 0.92,
                    "context_precision": 0.80,
                    "context_recall": 0.75,
                    "overall_score": 0.83
                },
                "retrieval_metrics": {
                    "recall_at_k": 0.8,
                    "precision_at_k": 0.6,
                    "mrr": 1.0,
                    "ndcg_at_k": 0.85
                },
                "evaluation_time_ms": 2500.0,
                "timestamp": "2024-01-01T12:00:00"
            }
        }


class BatchEvaluationRequest(BaseModel):
    """
    Request to evaluate multiple query-response pairs
    评估多个查询-响应对的请求

    Day 5: New model for batch evaluation
    Day 5： 批量评估的新模型
    """
    questions: List[str]
    answers: List[str]
    contexts_list: List[List[str]]
    ground_truths: Optional[List[str]] = None


class BatchEvaluationResponse(BaseModel):
    """
    Response containing batch evaluation results
    包含批量评估结果的响应

    Day 5: New model for batch evaluation response
    Day 5： 批量评估响应的新模型
    """
    results: List[EvaluationResponse]
    average_metrics: EvaluationMetrics
    total_evaluations: int
    total_time_ms: float


class TraceInfoResponse(BaseModel):
    """
    Response containing trace information
    包含追踪信息的响应

    Day 5: New model for tracing endpoint
    Day 5： 追踪端点的新模型
    """
    trace_id: str
    request_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    span_count: int = 0
    status: str = "OK"
