"""
LLM service using LangChain ChatOpenAI
使用 LangChain ChatOpenAI 的 LLM 服务

Day 4 Enhancement: Streaming support and anti-hallucination improvements
Day 4 增强： 流式输出支持和防幻觉改进
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings
from typing import List, Optional, AsyncIterator, Dict, Any


class LLMService:
    """
    Service for interacting with LLM using LangChain
    使用 LangChain 与 LLM 交互的服务

    Day 4: Added streaming support and enhanced prompts
    Day 4： 添加了流式支持和增强提示
    """

    # System prompt for RAG with strict anti-hallucination
    # 带严格防幻觉的 RAG 系统提示
    RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions STRICTLY based on the provided context documents.

CRITICAL RULES:
1. ONLY use information from the provided context documents
2. If the answer cannot be found in the context, say "I cannot find the answer in the provided documents."
3. DO NOT make up, infer, or hallucinate any information
4. When using information from the context, cite the source using [1], [2], etc. format
5. Always respond in the same language as the user's question

你是一个严格基于提供的上下文文档回答问题的助手。

关键规则：
1. 只使用提供的上下文文档中的信息
2. 如果答案无法在上下文中找到，请说"我在提供的文档中找不到答案。"
3. 不要编造、推断或幻觉任何信息
4. 使用上下文中的信息时，使用 [1], [2] 等格式引用来源
5. 始终用与用户问题相同的语言回答"""

    RAG_USER_PROMPT = """Based on the following context documents, please answer the question.

Remember:
- Use citation numbers [1], [2], etc. when referencing specific documents
- Only use information present in the context
- Say "I cannot find the answer" if the information is not in the context

Context Documents:
{context}

Question: {question}

---

请根据以下上下文文档回答问题。

请记住：
- 引用特定文档时使用引用编号 [1], [2] 等
- 只使用上下文中存在的信息
- 如果信息不在上下文中，请说"我找不到答案"

上下文文档:
{context}

问题: {question}"""

    def __init__(self):
        """
        Initialize the LLM service
        初始化 LLM 服务
        """
        self._llm: Optional[ChatOpenAI] = None
        self._streaming_llm: Optional[ChatOpenAI] = None
        self._chain = None

    def _get_llm(self, streaming: bool = False) -> ChatOpenAI:
        """
        Get or create LLM instance (lazy initialization)
        获取或创建 LLM 实例（延迟初始化）

        Day 4: Added streaming parameter
        Day 4： 添加了流式参数

        Args:
            streaming: Whether to enable streaming
                      是否启用流式传输
        """
        if streaming:
            if self._streaming_llm is None:
                kwargs = {
                    "model": settings.openai_model,
                    "api_key": settings.openai_api_key,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "streaming": True,
                }
                if settings.openai_api_base:
                    kwargs["base_url"] = settings.openai_api_base
                self._streaming_llm = ChatOpenAI(**kwargs)
            return self._streaming_llm

        if self._llm is None:
            # Build kwargs for ChatOpenAI
            # 构建 ChatOpenAI 的参数
            kwargs = {
                "model": settings.openai_model,
                "api_key": settings.openai_api_key,
                "temperature": 0.7,
                "max_tokens": 1000,
            }
            # Add base URL if configured
            # 如果配置了则添加 base URL
            if settings.openai_api_base:
                kwargs["base_url"] = settings.openai_api_base

            self._llm = ChatOpenAI(**kwargs)

            # Create prompt template
            # 创建提示模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.RAG_SYSTEM_PROMPT),
                ("human", self.RAG_USER_PROMPT),
            ])

            # Create chain
            # 创建链
            self._chain = prompt | self._llm | StrOutputParser()

        return self._llm

    @property
    def llm(self) -> ChatOpenAI:
        """
        Get the LangChain LLM instance
        获取 LangChain LLM 实例
        """
        return self._get_llm()

    async def generate_response(
        self,
        question: str,
        context: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response based on the question and context
        基于问题和上下文生成回答

        Args:
            question: User's question
                      用户的问题
            context: List of relevant text chunks
                     相关文本分块列表
            conversation_history: Previous conversation messages
                                  之前的对话消息
        Returns:
            Generated response
            生成的回答
        """
        # Ensure LLM is initialized
        # 确保 LLM 已初始化
        self._get_llm()

        # Build context string with citation markers
        # 构建带引用标记的上下文字符串
        context_text = "\n\n".join([
            f"[Document {i+1}]:\n{chunk}"
            for i, chunk in enumerate(context)
        ])

        # Invoke the chain
        # 调用链
        response = await self._chain.ainvoke({
            "context": context_text,
            "question": question,
        })

        return response

    async def generate_response_stream(
        self,
        question: str,
        context: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response based on the question and context
        基于问题和上下文生成流式回答

        Day 4: New method for streaming responses
        Day 4： 流式响应的新方法

        Args:
            question: User's question
                      用户的问题
            context: List of relevant text chunks
                     相关文本分块列表
            conversation_history: Previous conversation messages
                                  之前的对话消息
        Yields:
            Text chunks of the response
            响应的文本分块
        """
        # Get streaming LLM
        # 获取流式 LLM
        llm = self._get_llm(streaming=True)

        # Build context string with citation markers
        # 构建带引用标记的上下文字符串
        context_text = "\n\n".join([
            f"[Document {i+1}]:\n{chunk}"
            for i, chunk in enumerate(context)
        ])

        # Create prompt template
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.RAG_SYSTEM_PROMPT),
            ("human", self.RAG_USER_PROMPT),
        ])

        # Create messages
        # 创建消息
        messages = prompt.format_messages(
            context=context_text,
            question=question
        )

        # Stream the response
        # 流式传输响应
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text
        估计文本中的 token 数量

        Day 4: Helper method for context management
        Day 4： 上下文管理的辅助方法

        Args:
            text: Text to estimate
                  要估计的文本
        Returns:
            Estimated token count
            估计的 token 数量
        """
        # Simple estimation: ~4 characters per token for English
        # For Chinese, ~2 characters per token
        # 简单估计：英文约 4 字符/token，中文约 2 字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars

        estimated_tokens = (chinese_chars / 2) + (other_chars / 4)
        return int(estimated_tokens)

    def truncate_context(
        self,
        context: List[str],
        max_tokens: int = 3000
    ) -> List[str]:
        """
        Truncate context to fit within token limit
        截断上下文以适应 token 限制

        Day 4: New method for context management
        Day 4： 上下文管理的新方法

        Args:
            context: List of context chunks
                     上下文分块列表
            max_tokens: Maximum tokens allowed
                        允许的最大 token 数
        Returns:
            Truncated context list
            截断后的上下文列表
        """
        result = []
        current_tokens = 0

        for chunk in context:
            chunk_tokens = self.estimate_tokens(chunk)
            if current_tokens + chunk_tokens <= max_tokens:
                result.append(chunk)
                current_tokens += chunk_tokens
            else:
                # If we can't fit more, stop
                # 如果无法放入更多，停止
                break

        return result


# Global LLM service instance
# 全局 LLM 服务实例
llm_service = LLMService()
