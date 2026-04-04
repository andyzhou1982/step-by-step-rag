"""
QA History API routes for managing question-answer records
问答历史 API 路由，用于管理问答记录

Day 5 Feature: QA History for Evaluation
Day 5 功能： 用于评估的问答历史

Endpoints:
- GET /qa-history: List QA history with pagination
- GET /qa-history/{id}: Get single QA record
- DELETE /qa-history/{id}: Delete QA record
- POST /qa-history/export: Export QA records as JSON
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json

from models.schemas import (
    QAHistoryRecord,
    QAHistoryListResponse,
    QAHistoryExportRequest,
    ApiResponse,
)
from services.qa_history_service import qa_history_service
from config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/qa-history", tags=["QA History"])


@router.get("", response_model=QAHistoryListResponse)
async def list_qa_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID")
):
    """
    List QA history records with pagination
    分页列出问答历史记录

    Day 5: QA history list endpoint
    Day 5： 问答历史列表端点

    Returns:
        List of QA records with pagination info
        包含分页信息的问答记录列表
    """
    result = await qa_history_service.list_records(
        page=page,
        page_size=page_size,
        conversation_id=conversation_id
    )

    return QAHistoryListResponse(
        records=[QAHistoryRecord(**r) for r in result["records"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"]
    )


@router.get("/{record_id}", response_model=QAHistoryRecord)
async def get_qa_record(record_id: str):
    """
    Get a single QA record by ID
    根据 ID 获取单条问答记录

    Day 5: QA record detail endpoint
    Day 5： 问答记录详情端点

    Args:
        record_id: The QA record ID
                   问答记录 ID
    Returns:
        The QA record
        问答记录
    """
    record = await qa_history_service.get_record(record_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail="QA record not found / 问答记录未找到"
        )

    return QAHistoryRecord(**record)


@router.delete("/{record_id}", response_model=ApiResponse)
async def delete_qa_record(record_id: str):
    """
    Delete a QA record
    删除问答记录

    Day 5: QA record deletion endpoint
    Day 5： 问答记录删除端点

    Args:
        record_id: The QA record ID to delete
                   要删除的问答记录 ID
    Returns:
        Success status
        成功状态
    """
    success = await qa_history_service.delete_record(record_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="QA record not found / 问答记录未找到"
        )

    return ApiResponse(
        success=True,
        data={"deleted_id": record_id},
        error=None
    )


@router.post("/export")
async def export_qa_history(request: QAHistoryExportRequest):
    """
    Export QA history records as JSON
    导出问答历史记录为 JSON

    Day 5: QA history export endpoint
    Day 5： 问答历史导出端点

    Request body:
        record_ids: Optional list of specific record IDs to export
        conversation_id: Optional conversation ID to filter by

    Returns:
        JSON array of QA records suitable for evaluation
        适合评估的问答记录 JSON 数组
    """
    records = await qa_history_service.export_records(
        record_ids=request.record_ids,
        conversation_id=request.conversation_id
    )

    return {
        "records": records,
        "count": len(records),
        "export_format": "json"
    }


@router.get("/stats/summary")
async def get_qa_stats():
    """
    Get summary statistics of QA history
    获取问答历史统计摘要

    Day 5: QA statistics endpoint
    Day 5： 问答统计端点

    Returns:
        Summary statistics
        统计摘要
    """
    result = await qa_history_service.list_records(page=1, page_size=1)

    return {
        "total_records": result["total"],
        "service_status": "active"
    }
