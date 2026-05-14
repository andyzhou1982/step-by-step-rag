"""
Wiki API routes for knowledge compilation
知识编译的 Wiki API 路由

Day 8: REST API for Wiki page management, generation, and search
Day 8： Wiki 页面管理、生成和搜索的 REST API
"""

import time
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from models.schemas import (
    WikiPageInfo, WikiPageDetail, WikiPageListResponse,
    WikiGenerateRequest, WikiGenerateResponse,
    WikiSearchRequest, WikiSearchResult, ApiResponse
)
from services.wiki_store import wiki_store
from services.wiki_generator import wiki_generator
from services.concept_extractor import concept_extractor
from services.vector_store import vector_store
from config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/wiki", tags=["wiki"])


@router.get("/pages", response_model=WikiPageListResponse)
async def list_wiki_pages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    concept: Optional[str] = Query(None, description="Filter by concept tag")
):
    """
    List all Wiki pages with optional concept filter
    列出所有 Wiki 页面，可选概念过滤器
    """
    pages, total = await wiki_store.list_pages(limit, offset, concept)
    page_infos = []
    for p in pages:
        page_infos.append(WikiPageInfo(
            id=str(p.id),
            title=p.title,
            summary=p.summary,
            concepts=p.concepts or [],
            version=p.version,
            confidence=float(p.confidence) if p.confidence else 0.0,
            source_document_count=len(p.source_document_ids or []),
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))
    return WikiPageListResponse(pages=page_infos, total=total)


@router.get("/pages/{page_id}", response_model=WikiPageDetail)
async def get_wiki_page(page_id: str):
    """
    Get full Wiki page content by ID
    通过 ID 获取完整 Wiki 页面内容
    """
    page = await wiki_store.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail=f"Wiki page not found: {page_id}")

    # Get linked pages
    # 获取链接页面
    links = await wiki_store.get_page_links(page_id)

    return WikiPageDetail(
        id=str(page.id),
        title=page.title,
        content=page.content,
        summary=page.summary,
        concepts=page.concepts or [],
        source_document_ids=[str(did) for did in (page.source_document_ids or [])],
        source_chunk_ids=page.source_chunk_ids or [],
        version=page.version,
        confidence=float(page.confidence) if page.confidence else 0.0,
        generation_meta=page.generation_meta,
        linked_pages=links,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


@router.post("/generate", response_model=WikiGenerateResponse)
async def generate_wiki_pages(request: WikiGenerateRequest):
    """
    Generate Wiki pages from uploaded documents
    从上传的文档生成 Wiki 页面

    Day 8: Core endpoint - LLM reads documents, extracts concepts, generates Wiki
    Day 8： 核心端点 - LLM 阅读文档、提取概念、生成 Wiki
    """
    start_time = time.time()

    # Fetch all document chunks from vector store
    # 从向量存储获取所有文档分块
    try:
        all_chunks_raw = await vector_store.get_all_documents_for_bm25()
    except Exception as e:
        logger.error(f"Failed to fetch document chunks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read documents")

    if not all_chunks_raw:
        raise HTTPException(status_code=400, detail="No documents available. Please upload documents first.")

    # Convert to chunk format expected by concept extractor
    # 转换为概念提取器期望的分块格式
    all_chunks = [
        {
            "content": chunk.get("content", ""),
            "id": str(chunk.get("id", "")),
            "doc_id": chunk.get("metadata", {}).get("doc_id", ""),
            "filename": chunk.get("metadata", {}).get("filename", ""),
        }
        for chunk in all_chunks_raw
    ]

    # Filter by document IDs if specified
    # 如果指定了文档 ID 则进行过滤
    if request.document_ids:
        doc_id_set = set(request.document_ids)
        all_chunks = [c for c in all_chunks if c["doc_id"] in doc_id_set]

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No matching documents found.")

    # Step 1: Extract concepts from chunks
    # 步骤 1：从分块中提取概念
    logger.info(f"Extracting concepts from {len(all_chunks)} chunks...")
    concepts = await concept_extractor.extract_from_chunks(
        all_chunks,
        max_concepts_per_chunk=request.max_concepts_per_doc,
        max_total=request.max_pages
    )

    if not concepts:
        raise HTTPException(status_code=400, detail="No concepts could be extracted from the documents.")

    # Step 2: Generate Wiki pages for each concept
    # 步骤 2：为每个概念生成 Wiki 页面
    logger.info(f"Generating Wiki pages for {len(concepts)} concepts...")
    pages = await wiki_generator.generate_pages_from_concepts(
        concepts, all_chunks, max_pages=request.max_pages
    )

    if not pages:
        raise HTTPException(status_code=500, detail="Failed to generate any Wiki pages.")

    # Step 3: Save pages to database
    # 步骤 3：保存页面到数据库
    saved_pages = []
    for page_data in pages:
        try:
            # Check if page with same title already exists
            # 检查是否已存在相同标题的页面
            existing = await wiki_store.get_page_by_title(page_data["title"])
            if existing:
                # Update existing page
                # 更新现有页面
                updated = await wiki_store.update_page(
                    str(existing.id),
                    content=page_data["content"],
                    summary=page_data.get("summary", ""),
                    concepts=page_data.get("concepts", []),
                    confidence=page_data.get("confidence", 0.0)
                )
                if updated:
                    saved_pages.append(updated)
            else:
                # Create new page
                # 创建新页面
                saved = await wiki_store.save_page(
                    title=page_data["title"],
                    content=page_data["content"],
                    summary=page_data.get("summary", ""),
                    concepts=page_data.get("concepts", []),
                    source_document_ids=page_data.get("source_document_ids", []),
                    source_chunk_ids=page_data.get("source_chunk_ids", []),
                    confidence=page_data.get("confidence", 0.0),
                    generation_meta={"model": "llm-wiki"}
                )
                saved_pages.append(saved)
        except Exception as e:
            logger.warning(f"Failed to save Wiki page '{page_data['title']}': {e}")

    # Step 4: Auto-link pages based on concept overlap
    # 步骤 4：基于概念重叠自动链接页面
    links_created = 0
    try:
        links_created = await wiki_store.auto_link_pages(saved_pages)
    except Exception as e:
        logger.warning(f"Auto-linking failed: {e}")

    generation_time = (time.time() - start_time) * 1000

    logger.info(
        f"Wiki generation complete: {len(saved_pages)} pages, "
        f"{len(concepts)} concepts, {links_created} links in {generation_time:.0f}ms"
    )

    return WikiGenerateResponse(
        pages_generated=len(saved_pages),
        concepts_extracted=len(concepts),
        links_created=links_created,
        page_ids=[str(p.id) for p in saved_pages],
        generation_time_ms=generation_time
    )


@router.post("/search", response_model=list[WikiSearchResult])
async def search_wiki_pages(request: WikiSearchRequest):
    """
    Search Wiki pages using semantic similarity
    使用语义相似度搜索 Wiki 页面
    """
    results = await wiki_store.semantic_search(
        query=request.query,
        top_k=request.top_k,
        concept_filter=request.concept_filter
    )

    return [
        WikiSearchResult(
            page=WikiPageInfo(**r["page"]),
            score=r["score"],
            match_type=r["match_type"]
        )
        for r in results
    ]


@router.delete("/pages/{page_id}", response_model=ApiResponse)
async def delete_wiki_page(page_id: str):
    """
    Delete a Wiki page and its links
    删除 Wiki 页面及其链接
    """
    success = await wiki_store.delete_page(page_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Wiki page not found: {page_id}")
    return ApiResponse(success=True, data={"deleted": page_id})


@router.get("/concepts", response_model=list[str])
async def list_concepts():
    """
    List all unique concepts across all Wiki pages
    列出所有 Wiki 页面中的唯一概念
    """
    pages, _ = await wiki_store.list_pages(limit=1000)
    all_concepts = set()
    for page in pages:
        for concept in (page.concepts or []):
            all_concepts.add(concept)
    return sorted(list(all_concepts))


@router.get("/stats", response_model=dict)
async def wiki_stats():
    """
    Get Wiki system statistics
    获取 Wiki 系统统计信息
    """
    pages, total_pages = await wiki_store.list_pages(limit=1)
    all_pages, _ = await wiki_store.list_pages(limit=1000)

    all_concepts = set()
    total_source_docs = set()
    for page in all_pages:
        for c in (page.concepts or []):
            all_concepts.add(c)
        for doc_id in (page.source_document_ids or []):
            total_source_docs.add(str(doc_id))

    return {
        "total_pages": total_pages,
        "total_concepts": len(all_concepts),
        "total_source_documents": len(total_source_docs),
        "concepts": sorted(list(all_concepts))[:50]
    }
