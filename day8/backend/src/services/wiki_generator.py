"""
Wiki page generation service using LLM
使用 LLM 的 Wiki 页面生成服务

Day 8: Generates structured Wiki pages from document chunks and extracted concepts
Day 8： 从文档分块和提取的概念生成结构化 Wiki 页面
"""

import json
import time
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings, get_logger

logger = get_logger(__name__)


class WikiGenerator:
    """
    Generates structured Wiki pages from document content
    从文档内容生成结构化 Wiki 页面

    Day 8: Core service for the knowledge compilation pipeline
    Day 8： 知识编译流水线的核心服务
    """

    GENERATE_PROMPT = """You are a knowledge compiler. Your task is to generate a comprehensive, well-structured Wiki page for the given concept.

The Wiki page should:
1. Start with a clear, concise definition
2. Include detailed explanation with sub-sections
3. Provide examples where applicable
4. Reference related concepts
5. Be written in an encyclopedic style

Format the content in Markdown with:
- # Title (already provided)
- ## Sections for major topics
- ### Sub-sections for details
- Bullet points for lists
- **Bold** for key terms

IMPORTANT:
- ONLY use information from the provided source text
- Do NOT hallucinate or add external knowledge
- If the source text is insufficient, note it explicitly
- Write in the same language as the source text

你是一个知识编译器。你的任务是为给定的概念生成一个全面的、结构良好的 Wiki 页面。

Wiki 页面应该：
1. 以清晰简洁的定义开始
2. 包含带子章节的详细解释
3. 在适当的地方提供示例
4. 引用相关概念
5. 以百科全书风格编写

以 Markdown 格式编写内容，使用：
- # 标题（已提供）
- ## 主要章节
- ### 详细子章节
- 项目符号列表
- **加粗**关键术语

重要：
- 只使用提供的源文本中的信息
- 不要幻觉或添加外部知识
- 如果源文本不足，明确说明
- 用与源文本相同的语言编写"""

    async def generate_wiki_page(
        self,
        concept: Dict[str, Any],
        source_chunks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a Wiki page for a concept using source document chunks
        使用源文档分块为概念生成 Wiki 页面

        Args:
            concept: Concept dict with 'name', 'description', 'category'
                     包含 'name'、'description'、'category' 的概念字典
            source_chunks: Related document chunks with 'content' field
                           包含 'content' 字段的相关文档分块
        Returns:
            Generated Wiki page dict or None on failure
            生成的 Wiki 页面字典，失败时返回 None
        """
        concept_name = concept.get("name", "Unknown Concept")
        concept_desc = concept.get("description", "")

        # Combine relevant source chunks
        # 合并相关的源分块
        source_text = "\n\n---\n\n".join(
            chunk.get("content", "") for chunk in source_chunks[:10]
        )

        if not source_text.strip():
            logger.warning(f"No source text for concept: {concept_name}")
            return None

        try:
            llm = self._get_llm()
            messages = [
                SystemMessage(content=self.GENERATE_PROMPT),
                HumanMessage(content=f"""Generate a Wiki page for the concept: "{concept_name}"

Concept description: {concept_desc}

Source material:
{source_text[:4000]}""")
            ]
            response = await llm.ainvoke(messages)
            content = response.content.strip()

            # Extract summary (first non-heading paragraph)
            # 提取摘要（第一个非标题段落）
            summary = self._extract_summary(content)

            return {
                "title": concept_name,
                "content": content,
                "summary": summary,
                "concepts": [concept_name],
                "confidence": concept.get("importance", 3) / 5.0,
            }
        except Exception as e:
            logger.error(f"Wiki page generation failed for '{concept_name}': {e}", exc_info=True)
            return None

    async def generate_pages_from_concepts(
        self,
        concepts: List[Dict[str, Any]],
        all_chunks: List[Dict[str, Any]],
        max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Generate Wiki pages for multiple concepts
        为多个概念生成 Wiki 页面

        Args:
            concepts: List of concept dicts
                      概念字典列表
            all_chunks: All available document chunks
                        所有可用的文档分块
            max_pages: Maximum pages to generate
                       最大生成页面数
        Returns:
            List of generated Wiki page dicts
            生成的 Wiki 页面字典列表
        """
        pages: List[Dict[str, Any]] = []
        # Sort concepts by importance (highest first)
        # 按重要性排序概念（最高在前）
        sorted_concepts = sorted(
            concepts,
            key=lambda c: c.get("importance", 0),
            reverse=True
        )

        for concept in sorted_concepts[:max_pages]:
            # Find chunks related to this concept
            # 查找与此概念相关的分块
            related_chunks = self._find_related_chunks(concept, all_chunks)
            if not related_chunks:
                continue

            page = await self.generate_wiki_page(concept, related_chunks)
            if page:
                # Track which chunks contributed
                # 跟踪哪些分块有贡献
                page["source_chunk_ids"] = [
                    c.get("id", "") for c in related_chunks[:10]
                ]
                page["source_document_ids"] = list(set(
                    c.get("doc_id", "") for c in related_chunks[:10]
                    if c.get("doc_id")
                ))
                pages.append(page)
                logger.info(f"Generated Wiki page: {page['title']}")

        return pages

    def _find_related_chunks(
        self,
        concept: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        max_chunks: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find document chunks related to a concept using keyword matching
        使用关键词匹配查找与概念相关的文档分块
        """
        concept_name = concept.get("name", "").lower()
        concept_desc = concept.get("description", "").lower()
        # Split concept name into keywords
        # 将概念名称拆分为关键词
        keywords = set(concept_name.split()) | set(concept_desc.split()[:10])
        # Filter out common stop words
        # 过滤掉常见停用词
        stop_words = {"the", "a", "an", "is", "are", "of", "in", "to", "for", "and", "or", "的", "是", "在", "和"}
        keywords = keywords - stop_words

        scored_chunks: List[tuple] = []
        for chunk in chunks:
            content = chunk.get("content", "").lower()
            score = 0
            for kw in keywords:
                if kw in content:
                    score += content.count(kw)
            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by relevance score
        # 按相关性评分排序
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:max_chunks]]

    def _extract_summary(self, content: str) -> str:
        """
        Extract the first meaningful paragraph as summary
        提取第一个有意义的段落作为摘要
        """
        lines = content.split("\n")
        summary_parts: List[str] = []
        for line in lines:
            line = line.strip()
            # Skip headings and empty lines
            # 跳过标题和空行
            if not line or line.startswith("#"):
                if summary_parts:
                    break
                continue
            summary_parts.append(line)
            if len(" ".join(summary_parts)) > 300:
                break

        summary = " ".join(summary_parts)
        return summary[:500] if summary else ""

    def _get_llm(self) -> ChatOpenAI:
        """Get or create LLM instance / 获取或创建 LLM 实例"""
        kwargs = {
            "model": settings.openai_model,
            "openai_api_key": settings.openai_api_key,
            "temperature": 0.3,
            "max_tokens": 3000,
        }
        if settings.openai_api_base:
            kwargs["openai_api_base"] = settings.openai_api_base
        return ChatOpenAI(**kwargs)


# Global wiki generator instance
# 全局 Wiki 生成器实例
wiki_generator = WikiGenerator()
