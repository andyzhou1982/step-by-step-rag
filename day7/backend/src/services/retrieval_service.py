"""
Retrieval service with hybrid search, query rewriting, and re-ranking
支持混合检索、查询重写和重排序的检索服务

Day 3 Enhancement: Advanced retrieval strategies
Day 3 增强： 高级检索策略
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import re

# BM25 for keyword search
# 用于关键词搜索的 BM25
from rank_bm25 import BM25Okapi

# Chinese text segmentation
# 中文分词
import jieba

# LangChain components
# LangChain 组件
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings
from services.embedding import embedding_service


@dataclass
class SearchResult:
    """
    A single search result with content and metadata
    包含内容和元数据的单个搜索结果
    """
    chunk_id: str
    document_id: str
    content: str
    filename: str
    score: float
    file_type: str
    source: str  # "vector", "bm25", or "hybrid"


class BM25Index:
    """
    BM25 index for keyword-based search
    用于基于关键词搜索的 BM25 索引
    """

    def __init__(self):
        """
        Initialize BM25 index
        初始化 BM25 索引
        """
        self._index: Optional[BM25Okapi] = None
        self._documents: List[Dict] = []
        self._tokenized_docs: List[List[str]] = []

    def add_documents(self, documents: List[Dict]):
        """
        Add documents to the BM25 index
        将文档添加到 BM25 索引

        Args:
            documents: List of document dicts with 'content' and metadata
                      包含 'content' 和元数据的文档字典列表
        """
        self._documents = documents

        # Tokenize documents (simple whitespace + lowercase)
        # 分词（简单的空格 + 小写）
        self._tokenized_docs = [
            self._tokenize(doc.get('content', ''))
            for doc in documents
        ]

        # Create BM25 index
        # 创建 BM25 索引
        self._index = BM25Okapi(self._tokenized_docs)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 (supports Chinese and English)
        为 BM25 对文本进行分词（支持中英文）

        Args:
            text: Text to tokenize
                  要分词的文本
        Returns:
            List of tokens
            token 列表
        """
        if not text:
            return []

        # Check if text contains Chinese characters
        # 检查文本是否包含中文字符
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))

        if has_chinese:
            # Use jieba for Chinese text segmentation
            # 使用 jieba 进行中文分词
            tokens = list(jieba.cut(text))
        else:
            # Simple tokenization for English: lowercase and split
            # 英文简单分词：小写并分割
            text = text.lower()
            for char in '.,!?;:()[]{}"\'-–—\n\t':
                text = text.replace(char, ' ')
            tokens = text.split()

        # Filter out single-character tokens and stopwords
        # 过滤单字符 token 和停用词
        return [t.lower() for t in tokens if len(t.strip()) > 1]

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for documents using BM25
        使用 BM25 搜索文档

        Args:
            query: Search query
                   搜索查询
            top_k: Number of results to return
                   返回的结果数量
        Returns:
            List of (document_index, score) tuples
            (文档索引, 分数) 元组列表
        """
        if self._index is None:
            return []

        # Tokenize query
        # 对查询分词
        query_tokens = self._tokenize(query)

        # Get scores
        # 获取分数
        scores = self._index.get_scores(query_tokens)

        # Get top-k indices
        # 获取 top-k 索引
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [(int(idx), float(scores[idx])) for idx in top_indices]

    def get_document(self, index: int) -> Optional[Dict]:
        """
        Get document by index
        根据索引获取文档

        Args:
            index: Document index
                   文档索引
        Returns:
            Document dict or None
            文档字典或 None
        """
        if 0 <= index < len(self._documents):
            return self._documents[index]
        return None


class QueryRewriter:
    """
    Query rewriting service using LLM
    使用 LLM 的查询重写服务
    """

    REWRITE_PROMPT = """You are a query optimization assistant.
Given the user's question, generate an improved version that:
1. Clarifies ambiguous terms
2. Adds relevant synonyms or related terms
3. Maintains the original intent

Original question: {query}

Generate ONLY the improved question, nothing else.

你是一个查询优化助手。
给定用户的问题，生成一个改进版本：
1. 澄清模糊的术语
2. 添加相关同义词或相关术语
3. 保持原始意图

原始问题：{query}

只生成改进后的问题，不要其他内容。"""

    EXPAND_PROMPT = """Given the following question, generate 3 alternative versions that might help find relevant information.
Each version should use different wording or focus on different aspects.

Original question: {query}

Generate 3 alternative questions, one per line.

给定以下问题，生成 3 个可能有助于找到相关信息的替代版本。
每个版本应使用不同的措辞或关注不同的方面。

原始问题：{query}

生成 3 个替代问题，每行一个。"""

    def __init__(self):
        """
        Initialize query rewriter
        初始化查询重写器
        """
        self._llm: Optional[ChatOpenAI] = None

    def _get_llm(self) -> ChatOpenAI:
        """
        Get or create LLM instance
        获取或创建 LLM 实例
        """
        if self._llm is None:
            kwargs = {
                "model": settings.openai_model,
                "api_key": settings.openai_api_key,
                "temperature": 0.3,
                "max_tokens": 200,
            }
            if settings.openai_api_base:
                kwargs["base_url"] = settings.openai_api_base
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    async def rewrite_query(self, query: str) -> str:
        """
        Rewrite a query to improve search results
        重写查询以改善搜索结果

        Args:
            query: Original query
                   原始查询
        Returns:
            Rewritten query
                   重写后的查询
        """
        try:
            llm = self._get_llm()
            prompt = ChatPromptTemplate.from_template(self.REWRITE_PROMPT)
            chain = prompt | llm | StrOutputParser()

            result = await chain.ainvoke({"query": query})
            return result.strip()
        except Exception:
            # If rewriting fails, return original query
            # 如果重写失败，返回原始查询
            return query

    async def expand_query(self, query: str) -> List[str]:
        """
        Generate multiple query variations
        生成多个查询变体

        Args:
            query: Original query
                   原始查询
        Returns:
            List of query variations (including original)
            查询变体列表（包括原始查询）
        """
        try:
            llm = self._get_llm()
            prompt = ChatPromptTemplate.from_template(self.EXPAND_PROMPT)
            chain = prompt | llm | StrOutputParser()

            result = await chain.ainvoke({"query": query})
            variations = [v.strip() for v in result.strip().split('\n') if v.strip()]

            # Include original query
            # 包含原始查询
            return [query] + variations[:3]
        except Exception:
            # If expansion fails, return just original query
            # 如果扩展失败，只返回原始查询
            return [query]


class ReRanker:
    """
    Re-ranking service using cross-encoder or similarity
    使用交叉编码器或相似度的重排序服务
    """

    def __init__(self):
        """
        Initialize re-ranker
        初始化重排序器
        """
        self._model = None

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Re-rank search results based on relevance
        根据相关性对搜索结果进行重排序

        Args:
            query: Original query
                   原始查询
            results: Search results to re-rank
                     要重排序的搜索结果
            top_k: Number of results to return
                   返回的结果数量
        Returns:
            Re-ranked results
            重排序后的结果
        """
        if not results:
            return []

        try:
            # Use embedding similarity for re-ranking
            # 使用嵌入相似度进行重排序
            query_embedding = await embedding_service.embed_text(query)

            # Calculate similarity scores
            # 计算相似度分数
            reranked_results = []
            for result in results:
                content_embedding = await embedding_service.embed_text(result.content)

                # Cosine similarity
                # 余弦相似度
                similarity = self._cosine_similarity(query_embedding, content_embedding)

                # Combine original score with similarity
                # 将原始分数与相似度结合
                combined_score = 0.3 * result.score + 0.7 * similarity

                reranked_results.append(SearchResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    content=result.content,
                    filename=result.filename,
                    score=combined_score,
                    file_type=result.file_type,
                    source="reranked"
                ))

            # Sort by combined score
            # 按综合分数排序
            reranked_results.sort(key=lambda x: x.score, reverse=True)

            return reranked_results[:top_k]

        except Exception:
            # If re-ranking fails, return original results
            # 如果重排序失败，返回原始结果
            return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        计算两个向量之间的余弦相似度

        Args:
            vec1: First vector
                  第一个向量
            vec2: Second vector
                  第二个向量
        Returns:
            Cosine similarity score
            余弦相似度分数
        """
        a = np.array(vec1)
        b = np.array(vec2)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


class HybridRetrievalService:
    """
    Hybrid retrieval service combining vector and BM25 search
    结合向量搜索和 BM25 的混合检索服务
    """

    def __init__(self):
        """
        Initialize hybrid retrieval service
        初始化混合检索服务
        """
        self._bm25_index = BM25Index()
        self._query_rewriter = QueryRewriter()
        self._reranker = ReRanker()

        # Configuration
        # 配置
        self._vector_weight = 0.6  # Weight for vector search results
                                    # 向量搜索结果的权重
        self._bm25_weight = 0.4    # Weight for BM25 search results
                                    # BM25 搜索结果的权重

    def build_bm25_index(self, documents: List[Dict]):
        """
        Build BM25 index from documents
        从文档构建 BM25 索引

        Args:
            documents: List of document dicts
                      文档字典列表
        """
        self._bm25_index.add_documents(documents)

    async def search(
        self,
        query: str,
        vector_search_func,
        top_k: int = 5,
        use_rewrite: bool = False,
        use_rerank: bool = True
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector and BM25
        执行结合向量和 BM25 的混合搜索

        Args:
            query: Search query
                   搜索查询
            vector_search_func: Async function for vector search
                               用于向量搜索的异步函数
            top_k: Number of results to return
                   返回的结果数量
            use_rewrite: Whether to rewrite the query
                        是否重写查询
            use_rerank: Whether to re-rank results
                       是否重排序结果
        Returns:
            List of search results
            搜索结果列表
        """
        # Step 1: Optionally rewrite query
        # 步骤 1：可选地重写查询
        search_query = query
        if use_rewrite:
            search_query = await self._query_rewriter.rewrite_query(query)

        # Step 2: Perform parallel searches
        # 步骤 2：并行执行搜索
        vector_task = vector_search_func(search_query, top_k * 2)
        bm25_task = asyncio.create_task(
            asyncio.to_thread(self._bm25_search, search_query, top_k * 2)
        )

        vector_results = await vector_task
        bm25_results = await bm25_task

        # Step 3: Merge results with weighted scores
        # 步骤 3：使用加权分数合并结果
        merged_results = self._merge_results(
            vector_results, bm25_results, top_k * 2
        )

        # Step 4: Optionally re-rank
        # 步骤 4：可选地重排序
        if use_rerank and merged_results:
            merged_results = await self._reranker.rerank(
                query, merged_results, top_k
            )

        return merged_results[:top_k]

    def _bm25_search(self, query: str, top_k: int) -> List[SearchResult]:
        """
        Perform BM25 search
        执行 BM25 搜索

        Args:
            query: Search query
                   搜索查询
            top_k: Number of results
                   结果数量
        Returns:
            List of search results
            搜索结果列表
        """
        results = []
        bm25_results = self._bm25_index.search(query, top_k)

        for idx, score in bm25_results:
            doc = self._bm25_index.get_document(idx)
            if doc:
                results.append(SearchResult(
                    chunk_id=doc.get('chunk_id', ''),
                    document_id=doc.get('document_id', ''),
                    content=doc.get('content', ''),
                    filename=doc.get('filename', 'unknown'),
                    score=score,
                    file_type=doc.get('file_type', 'text'),
                    source='bm25'
                ))

        return results

    def _merge_results(
        self,
        vector_results: List[Tuple],
        bm25_results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """
        Merge vector and BM25 results with weighted scores
        使用加权分数合并向量和 BM25 结果

        Args:
            vector_results: Results from vector search
                           向量搜索结果
            bm25_results: Results from BM25 search
                         BM25 搜索结果
            top_k: Number of results to return
                   返回的结果数量
        Returns:
            Merged and sorted results
            合并并排序后的结果
        """
        # Normalize and combine scores
        # 归一化并合并分数
        merged = {}

        # Add vector results
        # 添加向量结果
        for result in vector_results:
            if len(result) == 6:
                chunk_id, doc_id, content, filename, score, file_type = result
            else:
                chunk_id, doc_id, content, filename, score = result[:5]
                file_type = "text"

            # Normalize score to 0-1 range
            # 将分数归一化到 0-1 范围
            normalized_score = max(0, min(1, score))

            merged[chunk_id] = SearchResult(
                chunk_id=chunk_id,
                document_id=doc_id,
                content=content,
                filename=filename,
                score=normalized_score * self._vector_weight,
                file_type=file_type,
                source='vector'
            )

        # Add BM25 results
        # 添加 BM25 结果
        for result in bm25_results:
            if result.chunk_id in merged:
                # Combine scores
                # 合并分数
                merged[result.chunk_id].score += result.score * self._bm25_weight
                merged[result.chunk_id].source = 'hybrid'
            else:
                # Add new result
                # 添加新结果
                merged[result.chunk_id] = SearchResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    content=result.content,
                    filename=result.filename,
                    score=result.score * self._bm25_weight,
                    file_type=result.file_type,
                    source='bm25'
                )

        # Sort by score and return
        # 按分数排序并返回
        sorted_results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:top_k]


# Global retrieval service instance
# 全局检索服务实例
retrieval_service = HybridRetrievalService()
