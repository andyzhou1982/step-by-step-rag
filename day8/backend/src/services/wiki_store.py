"""
Wiki page storage and retrieval service
Wiki 页面存储和检索服务

Day 8: CRUD operations, semantic search, and cross-reference management for Wiki pages
Day 8： Wiki 页面的 CRUD 操作、语义搜索和交叉引用管理
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import WikiPage, WikiLink, Base
from services.database_service import db_service
from services.embedding import embedding_service
from config import get_logger

logger = get_logger(__name__)


class WikiStore:
    """
    Storage service for Wiki pages with semantic search
    带语义搜索的 Wiki 页面存储服务

    Day 8: Manages Wiki page persistence, retrieval, and linking
    Day 8： 管理 Wiki 页面持久化、检索和链接
    """

    async def save_page(
        self,
        title: str,
        content: str,
        summary: str = "",
        concepts: Optional[List[str]] = None,
        source_document_ids: Optional[List[str]] = None,
        source_chunk_ids: Optional[List[str]] = None,
        confidence: float = 0.0,
        generation_meta: Optional[Dict] = None
    ) -> WikiPage:
        """
        Save a new Wiki page
        保存新的 Wiki 页面

        Args:
            title: Page title / 页面标题
            content: Page content in markdown / Markdown 格式的页面内容
            summary: Page summary / 页面摘要
            concepts: Extracted concepts / 提取的概念
            source_document_ids: Source document IDs / 源文档 ID
            source_chunk_ids: Source chunk IDs / 源分块 ID
            confidence: Confidence score / 置信度评分
            generation_meta: Generation metadata / 生成元数据
        Returns:
            Created WikiPage instance
            创建的 WikiPage 实例
        """
        async with await db_service.get_session() as session:
            page = WikiPage(
                id=uuid.uuid4(),
                title=title,
                content=content,
                summary=summary,
                concepts=concepts or [],
                source_document_ids=source_document_ids or [],
                source_chunk_ids=source_chunk_ids or [],
                confidence=confidence,
                generation_meta=generation_meta or {}
            )
            session.add(page)
            await session.commit()
            await session.refresh(page)

            # Generate and store embedding for semantic search
            # 生成并存储嵌入用于语义搜索
            await self._store_embedding(page)

            logger.info(f"Saved Wiki page: {title} (id={page.id})")
            return page

    async def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        concepts: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> Optional[WikiPage]:
        """
        Update an existing Wiki page
        更新现有 Wiki 页面
        """
        async with await db_service.get_session() as session:
            result = await session.execute(
                select(WikiPage).where(WikiPage.id == uuid.UUID(page_id))
            )
            page = result.scalar_one_or_none()
            if not page:
                return None

            if title is not None:
                page.title = title
            if content is not None:
                page.content = content
            if summary is not None:
                page.summary = summary
            if concepts is not None:
                page.concepts = concepts
            if confidence is not None:
                page.confidence = confidence

            page.version += 1
            from datetime import datetime
            page.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(page)

            # Update embedding if content changed
            # 内容变更时更新嵌入
            if content is not None:
                await self._store_embedding(page)

            return page

    async def get_page(self, page_id: str) -> Optional[WikiPage]:
        """
        Get a Wiki page by ID
        通过 ID 获取 Wiki 页面
        """
        async with await db_service.get_session() as session:
            result = await session.execute(
                select(WikiPage).where(WikiPage.id == uuid.UUID(page_id))
            )
            return result.scalar_one_or_none()

    async def get_page_by_title(self, title: str) -> Optional[WikiPage]:
        """
        Get a Wiki page by title
        通过标题获取 Wiki 页面
        """
        async with await db_service.get_session() as session:
            result = await session.execute(
                select(WikiPage).where(WikiPage.title == title)
            )
            return result.scalar_one_or_none()

    async def list_pages(
        self,
        limit: int = 50,
        offset: int = 0,
        concept_filter: Optional[str] = None
    ) -> tuple:
        """
        List Wiki pages with optional concept filter
        列出 Wiki 页面，可选概念过滤器

        Returns:
            Tuple of (pages, total_count)
            (页面列表, 总数) 的元组
        """
        async with await db_service.get_session() as session:
            query = select(WikiPage)
            count_query = select(func.count()).select_from(WikiPage)

            if concept_filter:
                # Filter by concept using JSONB contains
                # 使用 JSONB contains 按概念过滤
                filter_cond = WikiPage.concepts.contains([concept_filter])
                query = query.where(filter_cond)
                count_query = count_query.where(filter_cond)

            query = query.order_by(WikiPage.updated_at.desc()).offset(offset).limit(limit)

            result = await session.execute(query)
            pages = result.scalars().all()

            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            return list(pages), total

    async def delete_page(self, page_id: str) -> bool:
        """
        Delete a Wiki page and its links
        删除 Wiki 页面及其链接
        """
        async with await db_service.get_session() as session:
            page_uuid = uuid.UUID(page_id)
            # Delete related links first
            # 先删除相关链接
            await session.execute(
                delete(WikiLink).where(
                    or_(
                        WikiLink.source_page_id == page_uuid,
                        WikiLink.target_page_id == page_uuid
                    )
                )
            )
            # Delete the page
            # 删除页面
            result = await session.execute(
                delete(WikiPage).where(WikiPage.id == page_uuid)
            )
            await session.commit()
            return result.rowcount > 0

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        concept_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Wiki pages using semantic similarity
        使用语义相似度搜索 Wiki 页面

        Args:
            query: Search query / 搜索查询
            top_k: Number of results / 结果数量
            concept_filter: Optional concept filters / 可选的概念过滤器
        Returns:
            List of search results with scores
            带评分的搜索结果列表
        """
        # Generate query embedding
        # 生成查询嵌入
        query_embedding = await embedding_service.embed_text(query)

        # Use cosine similarity via SQL
        # 通过 SQL 使用余弦相似度
        async with await db_service.get_session() as session:
            # Use raw SQL for vector similarity search
            # 使用原始 SQL 进行向量相似度搜索
            embedding_str = str(query_embedding)

            filter_clause = ""
            if concept_filter:
                # Build concept filter conditions
                # 构建概念过滤条件
                conditions = []
                for concept in concept_filter:
                    conditions.append(f"concepts @> '[" + json.dumps(concept) + "]'")
                filter_clause = "AND (" + " OR ".join(conditions) + ")"

            sql = f"""
                SELECT id, title, summary, concepts, confidence, version,
                       created_at, updated_at,
                       1 - (embedding <=> '{embedding_str}'::vector) as similarity
                FROM wiki_page_embeddings
                WHERE TRUE {filter_clause}
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT :limit
            """

            try:
                result = await session.execute(
                    __import__('sqlalchemy').text(sql),
                    {"limit": top_k}
                )
                rows = result.fetchall()
                return [
                    {
                        "page": {
                            "id": str(row.id),
                            "title": row.title,
                            "summary": row.summary,
                            "concepts": row.concepts or [],
                            "version": row.version,
                            "confidence": float(row.confidence) if row.confidence else 0.0,
                            "created_at": row.created_at.isoformat() if row.created_at else None,
                            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                            "source_document_count": 0,
                        },
                        "score": float(row.similarity) if row.similarity else 0.0,
                        "match_type": "semantic"
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to keyword: {e}")
                return await self._keyword_search(session, query, top_k, concept_filter)

    async def _keyword_search(
        self,
        session: AsyncSession,
        query: str,
        top_k: int,
        concept_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback keyword search when vector search is unavailable
        向量搜索不可用时的回退关键词搜索
        """
        keywords = query.lower().split()
        query_builder = select(WikiPage)

        if concept_filter:
            for concept in concept_filter:
                query_builder = query_builder.where(
                    WikiPage.concepts.contains([concept])
                )

        result = await session.execute(
            query_builder.order_by(WikiPage.updated_at.desc()).limit(top_k * 2)
        )
        pages = result.scalars().all()

        # Score by keyword overlap
        # 按关键词重叠评分
        scored: List[tuple] = []
        for page in pages:
            text = f"{page.title} {page.summary or ''} {' '.join(page.concepts or [])}".lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, page))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "page": {
                    "id": str(p.id),
                    "title": p.title,
                    "summary": p.summary,
                    "concepts": p.concepts or [],
                    "version": p.version,
                    "confidence": float(p.confidence) if p.confidence else 0.0,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                    "source_document_count": 0,
                },
                "score": float(score) / len(keywords) if keywords else 0.0,
                "match_type": "keyword"
            }
            for score, p in scored[:top_k]
        ]

    async def add_link(
        self,
        source_page_id: str,
        target_page_id: str,
        relation_type: str = "related_to",
        confidence: float = 0.8
    ) -> WikiLink:
        """
        Create a cross-reference link between two Wiki pages
        创建两个 Wiki 页面之间的交叉引用链接
        """
        async with await db_service.get_session() as session:
            link = WikiLink(
                source_page_id=uuid.UUID(source_page_id),
                target_page_id=uuid.UUID(target_page_id),
                relation_type=relation_type,
                confidence=confidence
            )
            session.add(link)
            await session.commit()
            await session.refresh(link)
            return link

    async def get_page_links(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all links for a Wiki page (both outgoing and incoming)
        获取 Wiki 页面的所有链接（出站和入站）
        """
        async with await db_service.get_session() as session:
            page_uuid = uuid.UUID(page_id)
            result = await session.execute(
                select(WikiLink).where(
                    or_(
                        WikiLink.source_page_id == page_uuid,
                        WikiLink.target_page_id == page_uuid
                    )
                )
            )
            links = result.scalars().all()

            linked_pages: List[Dict[str, Any]] = []
            for link in links:
                # Determine the "other" page in this link
                # 确定此链接中的"另一"页面
                other_id = (
                    str(link.target_page_id)
                    if link.source_page_id == page_uuid
                    else str(link.source_page_id)
                )
                direction = (
                    "outgoing" if link.source_page_id == page_uuid
                    else "incoming"
                )
                # Fetch the linked page title
                # 获取链接页面标题
                other_page = await self.get_page(other_id)
                linked_pages.append({
                    "page_id": other_id,
                    "title": other_page.title if other_page else "Unknown",
                    "relation_type": link.relation_type,
                    "confidence": float(link.confidence) if link.confidence else 0.0,
                    "direction": direction
                })

            return linked_pages

    async def auto_link_pages(self, pages: List[WikiPage]) -> int:
        """
        Automatically create links between Wiki pages based on concept overlap
        基于概念重叠自动创建 Wiki 页面之间的链接

        Returns:
            Number of links created
            创建的链接数
        """
        links_created = 0
        for i, page_a in enumerate(pages):
            for page_b in pages[i + 1:]:
                # Check concept overlap
                # 检查概念重叠
                concepts_a = set(page_a.concepts or [])
                concepts_b = set(page_b.concepts or [])
                overlap = concepts_a & concepts_b

                if overlap:
                    confidence = len(overlap) / max(len(concepts_a | concepts_b), 1)
                    if confidence >= 0.1:
                        try:
                            await self.add_link(
                                str(page_a.id),
                                str(page_b.id),
                                relation_type="related_to",
                                confidence=confidence
                            )
                            links_created += 1
                        except Exception:
                            pass  # Link may already exist
        return links_created

    async def _store_embedding(self, page: WikiPage) -> None:
        """
        Store embedding vector for a Wiki page in a dedicated vector table
        在专用向量表中存储 Wiki 页面的嵌入向量
        """
        try:
            # Combine title + summary for embedding
            # 组合标题 + 摘要用于嵌入
            embed_text = f"{page.title}\n\n{page.summary or ''}"
            embedding = await embedding_service.embed_text(embed_text)

            # Use the vector_store's engine to insert into a wiki-specific table
            # 使用 vector_store 的引擎插入到 wiki 专用表
            from sqlalchemy import text
            async with db_service.engine.begin() as conn:
                # Create wiki embedding table if not exists
                # 如果不存在则创建 wiki 嵌入表
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS wiki_page_embeddings (
                        id UUID PRIMARY KEY,
                        title TEXT,
                        summary TEXT,
                        concepts JSONB DEFAULT '[]',
                        confidence FLOAT DEFAULT 0.0,
                        version INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        embedding vector
                    )
                """))

                # Upsert the embedding
                # 更新或插入嵌入
                embedding_str = str(embedding)
                await conn.execute(text("""
                    INSERT INTO wiki_page_embeddings (id, title, summary, concepts, confidence, version, embedding)
                    VALUES (:id, :title, :summary, :concepts::jsonb, :confidence, :version, :embedding::vector)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        concepts = EXCLUDED.concepts,
                        confidence = EXCLUDED.confidence,
                        version = EXCLUDED.version,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
                """), {
                    "id": str(page.id),
                    "title": page.title,
                    "summary": page.summary or "",
                    "concepts": json.dumps(page.concepts or []),
                    "confidence": page.confidence,
                    "version": page.version,
                    "embedding": embedding_str
                })
        except Exception as e:
            logger.warning(f"Failed to store Wiki page embedding: {e}", exc_info=True)


# Global wiki store instance
# 全局 Wiki 存储实例
wiki_store = WikiStore()
