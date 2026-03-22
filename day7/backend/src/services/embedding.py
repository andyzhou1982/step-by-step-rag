"""
Embedding service using LangChain OpenAI embeddings
使用 LangChain OpenAI 嵌入的嵌入服务
"""

from langchain_openai import OpenAIEmbeddings
from config import settings
from typing import List, Optional


class EmbeddingService:
    """
    Service for generating text embeddings using LangChain
    使用 LangChain 生成文本嵌入的服务
    """

    def __init__(self):
        """
        Initialize the embedding service
        初始化嵌入服务
        """
        self._embeddings: Optional[OpenAIEmbeddings] = None

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """
        Get or create embeddings instance (lazy initialization)
        获取或创建嵌入实例（延迟初始化）
        """
        if self._embeddings is None:
            # Build kwargs for OpenAI embeddings
            # 构建 OpenAI 嵌入的参数
            kwargs = {
                "model": settings.embedding_model,
                "openai_api_key": settings.openai_api_key,
            }
            # Add base URL if configured
            # 如果配置了则添加 base URL
            if settings.openai_api_base:
                kwargs["openai_api_base"] = settings.openai_api_base

            self._embeddings = OpenAIEmbeddings(**kwargs)
        return self._embeddings

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """
        Get the LangChain embeddings instance
        获取 LangChain 嵌入实例
        """
        return self._get_embeddings()

    async def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text to embedding vector
        将单个文本转换为嵌入向量

        Args:
            text: Input text to embed
                  需要嵌入的输入文本
        Returns:
            Embedding vector (list of floats)
            嵌入向量（浮点数列表）
        """
        return await self.embeddings.aembed_query(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert multiple texts to embedding vectors
        将多个文本转换为嵌入向量

        Args:
            texts: List of texts to embed
                   需要嵌入的文本列表
        Returns:
            List of embedding vectors
            嵌入向量列表
        """
        if not texts:
            return []
        return await self.embeddings.aembed_documents(texts)

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors
        获取嵌入向量的维度

        Returns:
            Dimension of embeddings
            嵌入的维度
        """
        # Common embedding dimensions
        # 常见嵌入维度
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(settings.embedding_model, 1536)


# Global embedding service instance
# 全局嵌入服务实例
embedding_service = EmbeddingService()
