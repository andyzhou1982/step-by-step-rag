"""
Citation service for tracking source references in LLM responses
在 LLM 响应中追踪源引用的引用溯源服务

Day 4 Enhancement: Citation extraction and confidence scoring
Day 4 增强： 引用提取和置信度评分
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


from services.retrieval_service import SearchResult


@dataclass
class Citation:
    """
    A citation reference in the answer
    答案中的引用参考

    Attributes:
        citation_id: The citation number (e.g., [1], [2])
                      引用编号（如 [1], [2]）
        chunk_id: The chunk ID being referenced
                     被引用的分块 ID
        document_id: The document ID
                      文档 ID
        filename: The filename of the source
                    源文件的文件名
        content: The relevant content snippet
                     相关内容片段
        relevance_score: How relevant this citation is (0-1)
                       此引用的相关性（0-1）
    """
    citation_id: int
    chunk_id: str
    document_id: str
    filename: str
    content: str
    relevance_score: float


class CitationService:
    """
    Service for extracting and managing citations from LLM responses
    从 LLM 响应中提取和管理引用的引用溯源服务

    Day 4: New service for citation management
    Day 4： 引用管理的新服务
    """

    # Pattern to match citations like [1], [2], [Source 1], etc.
    # 匹配引用的模式，如 [1], [2], [Source 1] 等
    CITATION_PATTERN = re.compile(r'\[(\d+)\]|\[Source\s*(\d+)\]|\[Doc\s*(\d+)\]', re.IGNORECASE)

    # Pattern to match document references like [Document 1], [Doc 1]
    # 匹配文档引用的模式，如 [Document 1], [Doc 1]
    DOC_PATTERN = re.compile(r'\[(?:Document|Doc)\s*(\d+)\]', re.IGNORECASE)

    def extract_citations(
        self,
        answer: str,
        sources: List[SearchResult]
    ) -> List[Citation]:
        """
        Extract citations from the answer text
        从答案文本中提取引用

        Args:
            answer: The LLM response text
                        LLM 响应文本
            sources: List of search results to match against
                       要匹配的搜索结果列表
        Returns:
            List of Citation objects
            Citation 对象列表
        """
        citations = []

        # Find all citation markers in the answer
        # 在答案中查找所有引用标记
        for match in self.CITATION_PATTERN.finditer(answer):
            # Get the first non-empty group (from multiple capture groups)
            # 获取第一个非空的捕获组
            citation_id = int(match.group(1) or match.group(2) or match.group(3))
            citations.append(Citation(
                citation_id=citation_id,
                chunk_id="",
                document_id="",
                filename="",
                content="",
                relevance_score=0.0
            ))

        # Match citations to sources
        # 将引用与来源匹配
        for citation in citations:
            # Find the matching source by citation ID
            # 通过引用 ID 找到匹配的来源
            if 0 < citation.citation_id <= len(sources):
                source = sources[citation.citation_id - 1]
                citation.chunk_id = source.chunk_id
                citation.document_id = source.document_id
                citation.filename = source.filename
                citation.content = source.content[:200] + "..." if len(source.content) > 200 else source.content
                citation.relevance_score = source.score

            else:
                # Citation ID out of range, assign to first available source
                # 引用 ID 躅出范围， 分配给第一个可用来源
                if sources:
                    source = sources[0]
                    citation.chunk_id = source.chunk_id
                    citation.document_id = source.document_id
                    citation.filename = source.filename
                    citation.content = source.content[:200] + "..." if len(source.content) > 200 else source.content

                    citation.relevance_score = source.score * 0.5

        return citations

    def calculate_confidence(
        self,
        answer: str,
        sources: List[SearchResult],
        citations: List[Citation]
    ) -> float:
        """
        Calculate confidence score based on context utilization
        基于上下文利用率计算置信度评分

        Day 4: Simple heuristic based on citation coverage
        Day 4： 基于引用覆盖率的简单启发式方法

        Args:
            answer: The LLM response
                        LLM 响应
            sources: Number of sources provided
                        提供的来源数量
            citations: Number of citations used
                        使用的引用数量
        Returns:
            Confidence score (0-1)
            置信度评分（0-1）
        """
        if not sources:
            return 0.0

        # Base confidence on number of relevant sources
        # 基础置信度基于相关来源的数量
        base_confidence = min(len(sources) / 5, 0.8)

        # Boost if citations are used
        # 如果使用了引用则提高置信度
        citation_boost = min(len(citations) / len(sources), 1.0) if sources else 0.0
        citation_boost = 0.3 * citation_boost

        # Penalty for "I cannot find" phrases
        # 对"我找不到"类短语进行惩罚
        lower_confidence = 0.0
        if "cannot find" in answer.lower() or "无法找到" in answer or "don't know" in answer.lower():
            lower_confidence = 0.3
        elif "no information" in answer.lower() or "没有信息" in answer.lower():
            lower_confidence = 0.2

        # Final confidence score
        # 最终置信度评分
        confidence = min(1.0, base_confidence + citation_boost - lower_confidence)
        return round(confidence, 2)

    def format_answer_with_citations(
        self,
        answer: str,
        sources: List[SearchResult]
    ) -> Tuple[str, List[Citation]]:
        """
        Format answer with inline citation markers
        格式化答案，内联引用标记

        Args:
            answer: The original answer text
                        原始答案文本
            sources: Sources to cite
                        要引用的来源
        Returns:
            Tuple of (formatted_answer, citations)
            (格式化答案, 引用) 元组
        """
        citations = self.extract_citations(answer, sources)

        # If no citations found, return as-is
        # 如果未找到引用，则原样返回
        if not citations:
            return answer, []

        # Return the answer with citations
        # 返回带引用的答案
        return answer, citations


# Global citation service instance
# 全局引用服务实例
citation_service = CitationService()
