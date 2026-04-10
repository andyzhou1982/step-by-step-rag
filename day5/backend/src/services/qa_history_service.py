"""
QA History service for persistent question-answer record storage
问答历史服务，用于持久化问答记录存储

Uses SQLAlchemy ORM for database operations
使用 SQLAlchemy ORM 进行数据库操作
"""

import uuid
import traceback
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import select, delete, func, and_

from config import settings, get_logger
from models.database import QAHistory
from services.database_service import db_service

logger = get_logger(__name__)


class QAHistoryService:
    """
    Service for managing QA history in PostgreSQL
    在 PostgreSQL 中管理问答历史的服务

    Uses SQLAlchemy ORM for database operations
    使用 SQLAlchemy ORM 进行数据库操作
    """

    def __init__(self):
        """
        Initialize the QA history service
        初始化问答历史服务

        No initialization needed - database is managed by db_service
        不需要初始化 - 数据库由 db_service 管理
        """
        pass

    async def connect(self):
        """
        Connect to the database (no-op for ORM)
        连接数据库（ORM 不需要此操作）

        The database connection is managed by db_service
        数据库连接由 db_service 管理
        """
        pass

    async def disconnect(self):
        """
        Disconnect from the database (no-op for ORM)
        断开数据库连接（ORM 不需要此操作）

        The database connection is managed by db_service
        数据库连接由 db_service 管理
        """
        pass

    async def add_record(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        sources: Optional[List[Dict]] = None,
        retrieval_method: Optional[str] = None,
        confidence: float = 0.0,
        conversation_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Add a QA record to the history
        将问答记录添加到历史

        Args:
            question: User's question / 用户问题
            answer: AI's answer / AI 回答
            contexts: Retrieved contexts / 检索到的上下文
            sources: Source references / 来源引用
            retrieval_method: Retrieval method used / 使用的检索方法
            confidence: Confidence score / 置信度评分
            conversation_id: Conversation ID / 对话 ID
        Returns:
            Record ID if successful, None otherwise
            成功返回记录 ID，否则返回 None
        """
        try:
            record_id = str(uuid.uuid4())
            async with db_service.session_factory() as session:
                record = QAHistory(
                    id=record_id,
                    question=question,
                    answer=answer,
                    contexts=contexts or [],
                    sources=sources or [],
                    retrieval_method=retrieval_method,
                    confidence=confidence,
                    created_at=datetime.utcnow(),
                    conversation_id=conversation_id,
                )
                session.add(record)
                await session.commit()
                logger.info(f"QA record saved: {record_id}")
                return record_id
        except Exception as e:
            logger.error(f"Error adding QA record: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return None

    async def get_record(self, record_id: str) -> Optional[Dict]:
        """
        Get a QA record by ID
        根据 ID 获取问答记录

        Args:
            record_id: Record ID / 记录 ID
        Returns:
            Record dict or None / 记录字典或 None
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(QAHistory).where(QAHistory.id == record_id)
                )
                record = result.scalar_one_or_none()

                if record:
                    return record.to_dict()
                return None
        except Exception as e:
            logger.error(f"Error getting QA record: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return None

    async def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        List QA records with pagination
        分页列出问答记录

        Args:
            page: Page number (1-indexed) / 页码（从 1 开始）
            page_size: Number of records per page / 每页记录数
            conversation_id: Filter by conversation ID / 按对话 ID 过滤
        Returns:
            Dict with records, total, page, page_size
            包含 records, total, page, page_size 的字典
        """
        try:
            offset = (page - 1) * page_size

            async with db_service.session_factory() as session:
                query = select(QAHistory)

                if conversation_id:
                    query = query.where(QAHistory.conversation_id == conversation_id)

                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar()

                # Get records with pagination
                query = query.order_by(QAHistory.created_at.desc())
                query = query.limit(page_size).offset(offset)

                result = await session.execute(query)
                records = result.scalars().all()

                return {
                    "records": [record.to_dict() for record in records],
                    "total": total or 0,
                    "page": page,
                    "page_size": page_size
                }
        except Exception as e:
            logger.error(f"Error listing QA records: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return {"records": [], "total": 0, "page": page, "page_size": page_size}

    async def delete_record(self, record_id: str) -> bool:
        """
        Delete a QA record
        删除问答记录

        Args:
            record_id: Record ID to delete / 要删除的记录 ID
        Returns:
            Whether deletion was successful / 删除是否成功
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    delete(QAHistory).where(QAHistory.id == record_id).returning(QAHistory.id)
                )
                await session.commit()
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error deleting QA record: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return False

    async def export_records(
        self,
        record_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Export QA records for evaluation
        导出问答记录用于评估

        Args:
            record_ids: Specific record IDs to export / 要导出的特定记录 ID
            conversation_id: Filter by conversation ID / 按对话 ID 过滤
        Returns:
            List of record dicts / 记录字典列表
        """
        try:
            async with db_service.session_factory() as session:
                query = select(QAHistory)

                conditions = []
                if record_ids:
                    conditions.append(QAHistory.id.in_(record_ids))
                if conversation_id:
                    conditions.append(QAHistory.conversation_id == conversation_id)

                if conditions:
                    query = query.where(and_(*conditions))

                query = query.order_by(QAHistory.created_at.desc())
                query = query.limit(10000)

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]
        except Exception as e:
            logger.error(f"Error exporting QA records: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return []


# Global QA history service instance
# 全局问答历史服务实例
qa_history_service = QAHistoryService()
