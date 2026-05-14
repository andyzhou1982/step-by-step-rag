"""
Concept extraction service using LLM
使用 LLM 的概念提取服务

Day 8: Extracts key concepts from document chunks for Wiki page generation
Day 8： 从文档分块中提取核心概念用于 Wiki 页面生成
"""

import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings, get_logger

logger = get_logger(__name__)


class ConceptExtractor:
    """
    Extracts key concepts from text using LLM
    使用 LLM 从文本中提取核心概念

    Day 8: Core component of the Wiki knowledge compilation pipeline
    Day 8： Wiki 知识编译流水线的核心组件
    """

    EXTRACT_PROMPT = """
你是一个知识分析师。从提供的文本中提取核心概念。

对每个概念，提供：
1. "name": 概念名称（简洁，2-5 个词）
2. "description": 简要说明（1-2 句话）
3. "category": 分类（如 "technology"、"methodology"、"entity"、"process"、"principle"）
4. "importance": 重要性评分（1-5，5 为最重要）

规则：
- 提取代表关键思想的概念，而不仅仅是频繁出现的词
- 合并相似概念（如 "RAG system" 和 "Retrieval-Augmented Generation" 应为一个概念）
- 专注于领域特定概念，而非通用术语
- 以 JSON 数组形式返回结果"""

    MERGE_PROMPT = """
你是一个知识组织者。给定从文档不同部分提取的多个概念列表，将它们合并为一个统一的、去重的列表。

规则：
- 合并指向同一事物的概念（即使名称不同）
- 保留最具描述性的名称
- 合并时组合描述
- 按重要性排序（最高在前）
- 以相同格式的 JSON 数组返回：name, description, category, importance"""

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None

    def _get_llm(self) -> ChatOpenAI:
        """Get or create LLM instance / 获取或创建 LLM 实例"""
        if self._llm is None:
            kwargs = {
                "model": settings.openai_model,
                "openai_api_key": settings.openai_api_key,
                "temperature": 0.1,
                "max_tokens": 2000,
            }
            if settings.openai_api_base:
                kwargs["openai_api_base"] = settings.openai_api_base
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    async def extract_concepts(
        self,
        text: str,
        max_concepts: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract key concepts from a text chunk
        从文本分块中提取核心概念

        Args:
            text: Input text to analyze
                  需要分析的输入文本
            max_concepts: Maximum number of concepts to extract
                          最大提取概念数
        Returns:
            List of concept dictionaries
            概念字典列表
        """
        try:
            llm = self._get_llm()
            messages = [
                SystemMessage(content=self.EXTRACT_PROMPT),
                HumanMessage(content=f"Extract up to {max_concepts} key concepts from this text:\n\n{text[:3000]}")
            ]
            response = await llm.ainvoke(messages)
            concepts = self._parse_json_response(response.content)
            return concepts[:max_concepts]
        except Exception as e:
            logger.warning(f"Concept extraction failed: {e}", exc_info=True)
            return []

    async def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        max_concepts_per_chunk: int = 5,
        max_total: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Extract concepts from multiple document chunks and merge
        从多个文档分块中提取概念并合并

        Args:
            chunks: List of chunks with 'content' field
                    包含 'content' 字段的分块列表
            max_concepts_per_chunk: Max concepts per chunk
                                    每个分块的最大概念数
            max_total: Maximum total concepts after merging
                       合并后的最大总概念数
        Returns:
            Merged and deduplicated concept list
            合并去重后的概念列表
        """
        all_concepts: List[Dict[str, Any]] = []

        for chunk in chunks:
            content = chunk.get("content", "")
            if not content or len(content.strip()) < 50:
                continue
            concepts = await self.extract_concepts(content, max_concepts_per_chunk)
            all_concepts.extend(concepts)

        if not all_concepts:
            return []

        # Merge and deduplicate concepts via LLM
        # 通过 LLM 合并和去重概念
        merged = await self._merge_concepts(all_concepts, max_total)
        return merged

    async def _merge_concepts(
        self,
        concepts: List[Dict[str, Any]],
        max_total: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate concept lists
        合并和去重概念列表
        """
        if len(concepts) <= max_total:
            # Simple dedup without LLM for small lists
            # 小列表无需 LLM 进行简单去重
            return self._simple_dedup(concepts)

        try:
            llm = self._get_llm()
            concepts_json = json.dumps(concepts, ensure_ascii=False)
            messages = [
                SystemMessage(content=self.MERGE_PROMPT),
                HumanMessage(content=f"Merge these concepts into at most {max_total} unique concepts:\n\n{concepts_json[:4000]}")
            ]
            response = await llm.ainvoke(messages)
            merged = self._parse_json_response(response.content)
            return merged[:max_total]
        except Exception as e:
            logger.warning(f"Concept merging failed, using simple dedup: {e}")
            return self._simple_dedup(concepts)[:max_total]

    def _simple_dedup(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simple deduplication by concept name (case-insensitive)
        通过概念名称的简单去重（不区分大小写）
        """
        seen: Dict[str, Dict[str, Any]] = {}
        for c in concepts:
            name = c.get("name", "").lower().strip()
            if name and name not in seen:
                seen[name] = c
            elif name in seen:
                # Keep the one with higher importance
                # 保留重要性更高的那个
                if c.get("importance", 0) > seen[name].get("importance", 0):
                    seen[name] = c
        return list(seen.values())

    def _parse_json_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse JSON from LLM response, handling markdown code blocks
        从 LLM 响应中解析 JSON，处理 markdown 代码块
        """
        text = response_text.strip()
        # Remove markdown code block wrapping
        # 移除 markdown 代码块包裹
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3]

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            # 尝试在响应中查找 JSON 数组
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    result = json.loads(text[start:end])
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass
            return []


# Global concept extractor instance
# 全局概念提取器实例
concept_extractor = ConceptExtractor()
