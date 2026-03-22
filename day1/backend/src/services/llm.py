"""
LLM service using LangChain ChatOpenAI
使用 LangChain ChatOpenAI 的 LLM 服务
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import settings
from typing import List, Optional


class LLMService:
    """
    Service for interacting with LLM using LangChain
    使用 LangChain 与 LLM 交互的服务
    """

    # System prompt for RAG
    # RAG 的系统提示
    RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.
If the answer cannot be found in the context, please say "I cannot find the answer in the provided documents." Do not make up information.
Always respond in the same language as the user's question.

你是一个基于提供上下文回答问题的助手。
如果答案无法在上下文中找到，请说"我在提供的文档中找不到答案。"不要编造信息。
始终用与用户问题相同的语言回答。"""

    RAG_USER_PROMPT = """Based on the following context, please answer the question.

Context:
{context}

Question: {question}

请根据以下上下文回答问题。

上下文:
{context}

问题: {question}"""

    def __init__(self):
        """
        Initialize the LLM service
        初始化 LLM 服务
        """
        self._llm: Optional[ChatOpenAI] = None
        self._chain = None

    def _get_llm(self) -> ChatOpenAI:
        """
        Get or create LLM instance (lazy initialization)
        获取或创建 LLM 实例（延迟初始化）
        """
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
        conversation_history: Optional[List[dict]] = None
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

        # Build context string
        # 构建上下文字符串
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


# Global LLM service instance
# 全局 LLM 服务实例
llm_service = LLMService()
