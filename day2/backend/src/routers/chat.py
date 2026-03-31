"""
Chat API routes for question answering
问答的聊天 API 路由

Day 2 Enhancement: Support for file type filtering in search
Day 2 增强： 支持搜索中的文件类型过滤
"""

import logging
import traceback

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import uuid

from models.schemas import ChatRequest, ChatResponse, SourceReference
from services.vector_store import vector_store
from services.llm import llm_service
from config import settings

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create router
# 创建路由器
router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory conversation storage (Day 2 still uses memory, Day 6 will add database)
# 内存对话存储（Day 2 仍使用内存，Day 6 将添加数据库）
conversations: Dict[str, List[dict]] = {}


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Answer a question based on uploaded documents
    基于上传文档回答问题

    Day 2 Enhancement: Supports file type filtering
    Day 2 增强： 支持文件类型过滤

    Args:
        request: Chat request containing the question and optional file type filter
                 包含问题和可选文件类型过滤器的聊天请求
    Returns:
        Chat response with answer and sources
        包含答案和来源的聊天响应
    """
    try:
        # Search for relevant documents
        # 搜索相关文档
        # Day 2: Pass file_types filter if provided
        # Day 2: 如果提供了 file_types 过滤器则传递
        search_results = await vector_store.search_similar(
            query=request.question,
            top_k=settings.top_k,
            file_types=request.file_types if hasattr(request, 'file_types') else None
        )

        if not search_results:
            return ChatResponse(
                answer="I couldn't find any relevant information in the uploaded documents. "
                       "Please try uploading some documents first.\n"
                       "我在上传的文档中找不到相关信息。请先尝试上传一些文档。",
                sources=[],
                conversation_id=request.conversation_id or str(uuid.uuid4())
            )

        # Extract context chunks
        # 提取上下文分块
        context_chunks: List[str] = []
        sources: List[SourceReference] = []

        # Day 2: Unpack 6 values instead of 5 (added file_type)
        # Day 2: 解包 6 个值而不是 5 个（添加了 file_type）
        for result in search_results:
            if len(result) == 6:
                chunk_id, doc_id, content, filename, score, file_type = result
            else:
                # Fallback for old format
                # 旧格式的回退
                chunk_id, doc_id, content, filename, score = result[:5]
                file_type = "text"

            context_chunks.append(content)
            # Truncate content for display
            # 截断内容用于显示
            display_content = content[:200] + "..." if len(content) > 200 else content
            sources.append(SourceReference(
                document_id=doc_id,
                filename=filename,
                content=display_content,
                score=round(score, 4),
                file_type=file_type
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
            conversation_id=conversation_id
        )

    except Exception as e:
        # Log the error with full traceback
        # 记录错误和完整堆栈
        logger.error(f"Error processing question: {str(e)}\n{traceback.format_exc()}")
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
