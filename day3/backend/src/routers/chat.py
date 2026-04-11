"""
Chat API routes for question answering
问答的聊天 API 路由

Day 3 Enhancement: Hybrid search, query rewriting, and re-ranking
Day 3 增强： 混合检索、查询重写和重排序
"""


from fastapi import APIRouter, HTTPException
from typing import Dict, List
import uuid

from models.schemas import (
    ChatRequest,
    ChatResponse,
    SourceReference,
    RetrievalConfig,
    RetrievalConfigResponse,
)
from services.vector_store import vector_store
from services.llm import llm_service
from services.retrieval_service import retrieval_service
from config import settings, get_logger

# Get logger for this module
# 获取此模块的日志记录器
logger = get_logger(__name__)

# Create router
# 创建路由器
router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory conversation storage (Day 3 still uses memory, Day 6 will add database)
# 内存对话存储（Day 3 仍使用内存，Day 6 将添加数据库）
conversations: Dict[str, List[dict]] = {}


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
async def get_retrieval_config():
    """
    Get current retrieval configuration
    获取当前检索配置

    Day 3: New endpoint to show retrieval settings
    Day 3： 新端点显示检索设置
    """
    config = RetrievalConfig(
        use_hybrid=settings.use_hybrid_search,
        use_rewrite=settings.use_query_rewrite,
        use_rerank=settings.use_rerank,
        top_k=settings.top_k,
        vector_weight=settings.vector_weight,
        bm25_weight=settings.bm25_weight,
    )
    return RetrievalConfigResponse(
        config=config,
        available_strategies=["vector", "bm25", "hybrid"],
        features=["query_rewrite", "rerank"]
    )


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Answer a question based on uploaded documents
    基于上传文档回答问题

    Day 3 Enhancement:
    - Hybrid search (vector + BM25)
    - Optional query rewriting
    - Optional re-ranking

    Day 3 增强：
    - 混合检索（向量 + BM25）
    - 可选的查询重写
    - 可选的重排序
    """
    try:
        # Get retrieval config from request or use defaults
        # 从请求获取检索配置或使用默认值
        config = request.retrieval_config or RetrievalConfig(
            use_hybrid=settings.use_hybrid_search,
            use_rewrite=settings.use_query_rewrite,
            use_rerank=settings.use_rerank,
            top_k=settings.top_k,
            vector_weight=settings.vector_weight,
            bm25_weight=settings.bm25_weight,
        )

        # Store original query for response
        # 保存原始查询用于响应
        original_query = request.question
        query_rewritten = False

        # Track retrieval method used
        # 追踪使用的检索方法
        retrieval_method = "hybrid" if config.use_hybrid else "vector"

        # Perform search
        # 执行搜索
        if config.use_hybrid:
            # Use hybrid search
            # 使用混合检索
            search_results = await retrieval_service.search(
                query=request.question,
                vector_search_func=lambda q, k: vector_store.search_similar(
                    query=q,
                    top_k=k,
                    file_types=request.file_types
                ),
                top_k=config.top_k,
                use_rewrite=config.use_rewrite,
                use_rerank=config.use_rerank,
            )
            # Check if query was rewritten
            # 检查查询是否被重写
            query_rewritten = config.use_rewrite
        else:
            # Use vector search only
            # 仅使用向量搜索
            search_results = await vector_store.search_similar(
                query=request.question,
                top_k=config.top_k,
                file_types=request.file_types
            )
            # Convert to SearchResult format
            # 转换为 SearchResult 格式
            from services.retrieval_service import SearchResult
            formatted_results = []
            for result in search_results:
                if len(result) == 6:
                    chunk_id, doc_id, content, filename, score, file_type = result
                else:
                    chunk_id, doc_id, content, filename, score = result[:5]
                    file_type = "text"
                formatted_results.append(SearchResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    content=content,
                    filename=filename,
                    score=score,
                    file_type=file_type,
                    source="vector"
                ))
            search_results = formatted_results
            retrieval_method = "vector"

        if not search_results:
            return ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents. "
                       "Please try uploading some documents first.\n"
                       "我在上传的文档中找不到相关信息。请先尝试上传一些文档。",
                sources=[],
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                retrieval_method=retrieval_method,
                query_rewritten=query_rewritten,
                original_query=original_query if query_rewritten else None,
            )

        # Extract context chunks and sources
        # 提取上下文分块和来源
        context_chunks: List[str] = []
        sources: List[SourceReference] = []

        for result in search_results:
            context_chunks.append(result.content)
            # Truncate content for display
            # 截断内容用于显示
            display_content = result.content[:200] + "..." if len(result.content) > 200 else result.content
            sources.append(SourceReference(
                document_id=result.document_id,
                filename=result.filename,
                content=display_content,
                score=round(result.score, 4),
                file_type=result.file_type,
            ))

        # Get or create conversation
        # 获取或创建对话
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conversation_history = conversations.get(conversation_id, [])

        # Generate answer using LLM
        # 使用 LLM 生成答案
        answer = await llm_service.generate_response(
            question=request.question,
            context=context_chunks,
            conversation_history=conversation_history
        )

        # Update conversation history
        # 更新对话历史
        conversations[conversation_id] = conversation_history + [
            {"role": "user", "content": request.question},
            {"role": "assistant", "content": answer}
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation_id,
            retrieval_method=retrieval_method,
            query_rewritten=query_rewritten,
            original_query=original_query if query_rewritten else None,
        )

    except Exception as e:
        # Log the error with full traceback
        # 记录错误和完整堆栈
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)} "
                   f"处理问题时出错: {str(e)}"
        )


@router.delete("/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history
    清除对话历史

    Args:
        conversation_id: ID of conversation to clear
                         要清除的对话 ID
    """
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"success": True, "message": "Conversation cleared"}
    return {"success": False, "message": "Conversation not found"}
