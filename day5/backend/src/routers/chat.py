"""
Chat API routes for question answering
问答的聊天 API 路由

Day 3 Enhancement: Hybrid search, query rewriting, and re-ranking
Day 3 增强： 混合检索、查询重写和重排序

Day 4 Enhancement: Streaming, citations, confidence scoring
Day 4 增强： 流式输出、引用溯源、置信度评分
"""

import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, List
import uuid
import json
from datetime import datetime

from models.schemas import (
    ChatRequest,
    ChatResponse,
    SourceReference,
    RetrievalConfig,
    RetrievalConfigResponse,
    StreamChunk,
    ConversationHistory,
    ConversationMessage,
    ConversationSummary,
)
from services.vector_store import vector_store
from services.llm import llm_service
from services.retrieval_service import retrieval_service, SearchResult
from services.citation_service import citation_service
from config import settings, get_logger

# Get logger for this module
# 获取此模块的日志记录器
logger = get_logger(__name__)

# Create router
# 创建路由器
router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory conversation storage with metadata
# 带元数据的内存对话存储
# Structure: {conversation_id: {"messages": [...], "created_at": datetime, "updated_at": datetime}}
# 结构：{conversation_id: {"messages": [...], "created_at": datetime, "updated_at": datetime}}
conversations: Dict[str, Dict] = {}

# Maximum messages to keep in conversation history
# 对话历史中保留的最大消息数
MAX_HISTORY_MESSAGES = 20


@router.get("/retrieval-config", response_model=RetrievalConfigResponse)
async def get_retrieval_config():
    """
    Get current retrieval configuration
    获取当前检索配置

    Day 3: New endpoint to show retrieval settings
    Day 3： 新端点显示检索设置

    Day 4: Added streaming and citations to features
    Day 4： 在功能中添加了流式输出和引用
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
        features=["query_rewrite", "rerank", "streaming", "citations"]
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations():
    """
    List all conversations
    列出所有对话

    Day 4: New endpoint for conversation management
    Day 4： 对话管理的新端点
    """
    summaries = []
    for conv_id, conv_data in conversations.items():
        messages = conv_data.get("messages", [])
        if messages:
            # Get preview from last message
            # 从最后一条消息获取预览
            last_message = messages[-1]
            preview = last_message.get("content", "")[:100]

            summaries.append(ConversationSummary(
                conversation_id=conv_id,
                preview=preview,
                message_count=len(messages),
                created_at=conv_data.get("created_at", datetime.now()),
                last_updated=conv_data.get("updated_at", datetime.now()),
            ))

    # Sort by last updated
    # 按最后更新时间排序
    summaries.sort(key=lambda x: x.last_updated, reverse=True)
    return summaries


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """
    Get conversation history
    获取对话历史

    Day 4: New endpoint for conversation retrieval
    Day 4： 对话检索的新端点
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found / 对话未找到"
        )

    conv_data = conversations[conversation_id]
    messages = [
        ConversationMessage(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            timestamp=msg.get("timestamp", datetime.now()),
            sources=msg.get("sources"),
        )
        for msg in conv_data.get("messages", [])
    ]

    return ConversationHistory(
        conversation_id=conversation_id,
        messages=messages,
        message_count=len(messages),
        created_at=conv_data.get("created_at", datetime.now()),
        last_updated=conv_data.get("updated_at", datetime.now()),
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

    Day 4 Enhancement:
    - Citation tracking
    - Confidence scoring
    - Context-aware response

    Day 4 增强：
    - 引用追踪
    - 置信度评分
    - 上下文感知响应
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
            raw_results = await vector_store.search_similar(
                query=request.question,
                top_k=config.top_k,
                file_types=request.file_types
            )
            # Convert to SearchResult format
            # 转换为 SearchResult 格式
            search_results = []
            for result in raw_results:
                if len(result) == 6:
                    chunk_id, doc_id, content, filename, score, file_type = result
                else:
                    chunk_id, doc_id, content, filename, score = result[:5]
                    file_type = "text"
                search_results.append(SearchResult(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    content=content,
                    filename=filename,
                    score=score,
                    file_type=file_type,
                    source="vector"
                ))
            retrieval_method = "vector"

        # Get or create conversation
        # 获取或创建对话
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conversation_history = _get_conversation_history(conversation_id)

        if not search_results:
            # No results found
            # 未找到结果
            empty_response = ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents. "
                       "Please try uploading some documents first.\n"
                       "我在上传的文档中找不到相关信息。请先尝试上传一些文档。",
                sources=[],
                conversation_id=conversation_id,
                retrieval_method=retrieval_method,
                query_rewritten=query_rewritten,
                original_query=original_query if query_rewritten else None,
                confidence=0.0,
                is_context_based=False,
                context_tokens=0,
            )
            _update_conversation(conversation_id, request.question, empty_response.answer, [])
            return empty_response

        # Extract context chunks and sources with citation IDs
        # 提取带引用 ID 的上下文分块和来源
        context_chunks: List[str] = []
        sources: List[SourceReference] = []

        # Day 4: Truncate context to fit token limit
        # Day 4： 截断上下文以适应 token 限制
        for i, result in enumerate(search_results):
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
                source=result.source,
                citation_id=i + 1,  # Day 4: Citation ID (1-based)
            ))

        # Day 4: Truncate context if needed
        # Day 4： 如果需要则截断上下文
        context_chunks = llm_service.truncate_context(
            context_chunks,
            max_tokens=request.max_context_tokens
        )

        # Estimate context tokens
        # 估计上下文 token 数
        context_tokens = sum(llm_service.estimate_tokens(chunk) for chunk in context_chunks)

        # Generate answer using LLM
        # 使用 LLM 生成答案
        answer = await llm_service.generate_response(
            question=request.question,
            context=context_chunks,
            conversation_history=conversation_history
        )

        # Day 4: Calculate confidence score
        # Day 4： 计算置信度评分
        citations = citation_service.extract_citations(answer, search_results)
        confidence = citation_service.calculate_confidence(
            answer, search_results, citations
        )

        # Day 4: Check if answer is context-based
        # Day 4： 检查答案是否基于上下文
        is_context_based = _is_context_based(answer)

        # Update conversation history
        # 更新对话历史
        _update_conversation(conversation_id, request.question, answer, sources)

        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation_id,
            retrieval_method=retrieval_method,
            query_rewritten=query_rewritten,
            original_query=original_query if query_rewritten else None,
            confidence=confidence,
            is_context_based=is_context_based,
            context_tokens=context_tokens,
        )

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)} "
                   f"处理问题时出错: {str(e)}"
        )


@router.post("/stream")
async def stream_answer(request: ChatRequest):
    """
    Stream answer based on uploaded documents (SSE)
    基于上传文档流式回答（SSE）

    Day 4: New endpoint for streaming responses
    Day 4： 流式响应的新端点
    """

    async def generate():
        try:
            # Get retrieval config
            # 获取检索配置
            config = request.retrieval_config or RetrievalConfig(
                use_hybrid=settings.use_hybrid_search,
                use_rewrite=settings.use_query_rewrite,
                use_rerank=settings.use_rerank,
                top_k=settings.top_k,
                vector_weight=settings.vector_weight,
                bm25_weight=settings.bm25_weight,
            )

            original_query = request.question
            query_rewritten = False
            retrieval_method = "hybrid" if config.use_hybrid else "vector"

            # Perform search
            # 执行搜索
            if config.use_hybrid:
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
                query_rewritten = config.use_rewrite
            else:
                raw_results = await vector_store.search_similar(
                    query=request.question,
                    top_k=config.top_k,
                    file_types=request.file_types
                )
                search_results = []
                for result in raw_results:
                    if len(result) == 6:
                        chunk_id, doc_id, content, filename, score, file_type = result
                    else:
                        chunk_id, doc_id, content, filename, score = result[:5]
                        file_type = "text"
                    search_results.append(SearchResult(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        content=content,
                        filename=filename,
                        score=score,
                        file_type=file_type,
                        source="vector"
                    ))
                retrieval_method = "vector"

            conversation_id = request.conversation_id or str(uuid.uuid4())

            if not search_results:
                # Send error chunk
                # 发送错误分块
                error_chunk = StreamChunk(
                    type="error",
                    error="No relevant information found",
                    conversation_id=conversation_id,
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"

                done_chunk = StreamChunk(type="done", conversation_id=conversation_id)
                yield f"data: {done_chunk.model_dump_json()}\n\n"
                return

            # Prepare sources with citation IDs
            # 准备带引用 ID 的来源
            sources = []
            context_chunks = []
            for i, result in enumerate(search_results):
                context_chunks.append(result.content)
                display_content = result.content[:200] + "..." if len(result.content) > 200 else result.content
                sources.append(SourceReference(
                    document_id=result.document_id,
                    filename=result.filename,
                    content=display_content,
                    score=round(result.score, 4),
                    file_type=result.file_type,
                    source=result.source,
                    citation_id=i + 1,
                ))

            # Truncate context
            # 截断上下文
            context_chunks = llm_service.truncate_context(
                context_chunks,
                max_tokens=request.max_context_tokens
            )

            # Send sources first
            # 首先发送来源
            sources_chunk = StreamChunk(
                type="sources",
                sources=sources,
                conversation_id=conversation_id,
            )
            yield f"data: {sources_chunk.model_dump_json()}\n\n"

            # Stream the answer
            # 流式传输答案
            full_answer = ""
            async for text_chunk in llm_service.generate_response_stream(
                question=request.question,
                context=context_chunks,
                conversation_history=_get_conversation_history(conversation_id),
            ):
                full_answer += text_chunk
                content_chunk = StreamChunk(
                    type="content",
                    content=text_chunk,
                    conversation_id=conversation_id,
                )
                yield f"data: {content_chunk.model_dump_json()}\n\n"

            # Calculate confidence
            # 计算置信度
            citations = citation_service.extract_citations(full_answer, search_results)
            confidence = citation_service.calculate_confidence(
                full_answer, search_results, citations
            )

            # Send done chunk
            # 发送完成分块
            done_chunk = StreamChunk(
                type="done",
                conversation_id=conversation_id,
                confidence=confidence,
            )
            yield f"data: {done_chunk.model_dump_json()}\n\n"

            # Update conversation
            # 更新对话
            _update_conversation(conversation_id, request.question, full_answer, sources)

        except Exception as e:
            # Log the error with full traceback
            # 记录错误和完整堆栈
            logger.error(f"Stream error: {str(e)}")
            logger.debug(traceback.format_exc())
            error_chunk = StreamChunk(
                type="error",
                error=str(e),
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.delete("/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history
    清除对话历史

    Day 4: Enhanced with better response
    Day 4： 增强了响应
    """
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"success": True, "message": "Conversation cleared / 对话已清除"}
    return {"success": False, "message": "Conversation not found / 对话未找到"}


# ==================== Helper Functions ====================
# ==================== 辅助函数 ====================

def _get_conversation_history(conversation_id: str) -> List[Dict]:
    """
    Get conversation history for a given ID
    获取给定 ID 的对话历史

    Day 4: Helper function with history limiting
    Day 4： 带历史限制的辅助函数
    """
    if conversation_id not in conversations:
        return []

    messages = conversations[conversation_id].get("messages", [])

    # Limit to last N messages
    # 限制为最近 N 条消息
    if len(messages) > MAX_HISTORY_MESSAGES:
        messages = messages[-MAX_HISTORY_MESSAGES:]

    return messages


def _update_conversation(
    conversation_id: str,
    question: str,
    answer: str,
    sources: List[SourceReference]
):
    """
    Update conversation with new message pair
    用新消息对更新对话

    Day 4: Helper function for conversation management
    Day 4： 对话管理的辅助函数
    """
    now = datetime.now()

    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }

    conv = conversations[conversation_id]
    conv["messages"].extend([
        {
            "role": "user",
            "content": question,
            "timestamp": now,
        },
        {
            "role": "assistant",
            "content": answer,
            "timestamp": now,
            "sources": sources,
        }
    ])
    conv["updated_at"] = now

    # Trim history if too long
    # 如果历史过长则修剪
    if len(conv["messages"]) > MAX_HISTORY_MESSAGES * 2:
        conv["messages"] = conv["messages"][-MAX_HISTORY_MESSAGES * 2:]


def _is_context_based(answer: str) -> bool:
    """
    Check if the answer is based on context
    检查答案是否基于上下文

    Day 4: Heuristic to detect context-based answers
    Day 4： 检测基于上下文答案的启发式方法
    """
    lower_answer = answer.lower()

    # Phrases indicating no context was used
    # 表示未使用上下文的短语
    no_context_phrases = [
        "i cannot find",
        "i can't find",
        "no information",
        "not mentioned",
        "don't have",
        "doesn't contain",
        "我找不到",
        "无法找到",
        "没有找到",
        "未提及",
        "不包含",
    ]

    for phrase in no_context_phrases:
        if phrase in lower_answer:
            return False

    return True
