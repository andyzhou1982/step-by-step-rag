"""
QA History service for persistent question-answer record storage
问答历史服务，用于持久化问答记录存储

Day 5 Enhancement: Store QA history for evaluation purposes
Day 5 增强：存储问答历史用于评估
"""

import uuid
import traceback
import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings, get_logger

logger = get_logger(__name__)


class QAHistoryService:
    """
    Service for managing QA history in PostgreSQL
    在 PostgreSQL 中管理问答历史的服务
    """

    def __init__(self):
        """
        Initialize the QA history service
        初始化问答历史服务
        """
        self._connection_string = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self._async_engine = None
        self._table_name = "qa_history"

    async def connect(self):
        """
        Connect to the database and initialize the QA history table
        连接数据库并初始化问答历史表
        """
        self._async_engine = create_async_engine(self._connection_string)

        # Create table if not exists
        # 如果表不存在则创建
        async with self._async_engine.connect() as conn:
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id VARCHAR(36) PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    contexts JSONB NOT NULL DEFAULT '[]',
                    sources JSONB DEFAULT '{{}}',
                    retrieval_method VARCHAR(50),
                    confidence FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    conversation_id VARCHAR(36)
                )
            """))
            # Create index on created_at for efficient ordering
            # 在 created_at 上创建索引以提高排序效率
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_qa_history_created_at
                ON {self._table_name} (created_at DESC)
            """))
            await conn.commit()
        logger.info("QA history table initialized")

    async def disconnect(self):
        """
        Disconnect from the database
        断开数据库连接
        """
        if self._async_engine:
            await self._async_engine.dispose()
        self._async_engine = None

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
            async with self._async_engine.connect() as conn:
                await conn.execute(text(f"""
                    INSERT INTO {self._table_name}
                    (id, question, answer, contexts, sources, retrieval_method,
                     confidence, created_at, conversation_id)
                    VALUES (:id, :question, :answer, :contexts, :sources,
                            :retrieval_method, :confidence, :created_at, :conversation_id)
                """), {
                    "id": record_id,
                    "question": question,
                    "answer": answer,
                    "contexts": json.dumps(contexts),
                    "sources": json.dumps(sources or []),
                    "retrieval_method": retrieval_method,
                    "confidence": confidence,
                    "created_at": datetime.now(),
                    "conversation_id": conversation_id
                })
                await conn.commit()
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
            async with self._async_engine.connect() as conn:
                result = await conn.execute(text(f"""
                    SELECT id, question, answer, contexts, sources,
                           retrieval_method, confidence, created_at, conversation_id
                    FROM {self._table_name}
                    WHERE id = :id
                """), {"id": record_id})
                row = result.fetchone()
                if row:
                    return {
                        "id": row.id,
                        "question": row.question,
                        "answer": row.answer,
                        "contexts": row.contexts if isinstance(row.contexts, list) else json.loads(row.contexts or '[]'),
                        "sources": row.sources if isinstance(row.sources, list) else json.loads(row.sources or '[]'),
                        "retrieval_method": row.retrieval_method,
                        "confidence": float(row.confidence or 0.0),
                        "created_at": row.created_at,
                        "conversation_id": row.conversation_id
                    }
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

            # Build filter condition
            # 构建过滤条件
            where_clause = ""
            params = {"offset": offset, "limit": page_size}
            if conversation_id:
                where_clause = "WHERE conversation_id = :conversation_id"
                params["conversation_id"] = conversation_id

            async with self._async_engine.connect() as conn:
                # Get total count
                # 获取总数
                count_result = await conn.execute(text(f"""
                    SELECT COUNT(*) as total FROM {self._table_name} {where_clause}
                """), {k: v for k, v in params.items() if k != "offset" and k != "limit"})
                total = count_result.fetchone().total

                # Get records
                # 获取记录
                result = await conn.execute(text(f"""
                    SELECT id, question, answer, contexts, sources,
                           retrieval_method, confidence, created_at, conversation_id
                    FROM {self._table_name}
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """), params)
                rows = result.fetchall()

                records = []
                for row in rows:
                    records.append({
                        "id": row.id,
                        "question": row.question,
                        "answer": row.answer,
                        "contexts": row.contexts if isinstance(row.contexts, list) else json.loads(row.contexts or '[]'),
                        "sources": row.sources if isinstance(row.sources, list) else json.loads(row.sources or '[]'),
                        "retrieval_method": row.retrieval_method,
                        "confidence": float(row.confidence or 0.0),
                        "created_at": row.created_at,
                        "conversation_id": row.conversation_id
                    })

                return {
                    "records": records,
                    "total": total,
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
            async with self._async_engine.connect() as conn:
                result = await conn.execute(text(f"""
                    DELETE FROM {self._table_name}
                    WHERE id = :id
                    RETURNING id
                """), {"id": record_id})
                await conn.commit()
                return result.fetchone() is not None
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
            async with self._async_engine.connect() as conn:
                query = f"""
                    SELECT id, question, answer, contexts, sources,
                           retrieval_method, confidence, created_at, conversation_id
                    FROM {self._table_name}
                """
                conditions = []
                params = {}

                if record_ids:
                    conditions.append("id = ANY(:ids)")
                    params["ids"] = record_ids
                if conversation_id:
                    conditions.append("conversation_id = :conversation_id")
                    params["conversation_id"] = conversation_id

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY created_at DESC"

                result = await conn.execute(text(query), params)
                rows = result.fetchall()

                records = []
                for row in rows:
                    records.append({
                        "id": row.id,
                        "question": row.question,
                        "answer": row.answer,
                        "contexts": row.contexts if isinstance(row.contexts, list) else json.loads(row.contexts or '[]'),
                        "sources": row.sources if isinstance(row.sources, list) else json.loads(row.sources or '[]'),
                        "retrieval_method": row.retrieval_method,
                        "confidence": float(row.confidence or 0.0),
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "conversation_id": row.conversation_id
                    })

                return records
        except Exception as e:
            logger.error(f"Error exporting QA records: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return []


# Global QA history service instance
# 全局问答历史服务实例
qa_history_service = QAHistoryService()
