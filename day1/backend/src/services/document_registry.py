"""
Document registry service for persistent document metadata storage
文档注册表服务，用于持久化文档元数据存储

Uses SQLAlchemy ORM for database operations
使用 SQLAlchemy ORM 进行数据库操作
"""

import traceback
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import select, delete

from config import settings, get_logger
from models.database import DocumentRegistry
from services.database_service import db_service

logger = get_logger(__name__)


class DocumentRegistryService:
    """
    Service for managing document metadata in PostgreSQL
    在 PostgreSQL 中管理文档元数据的服务

    Uses SQLAlchemy ORM for database operations
    使用 SQLAlchemy ORM 进行数据库操作
    """

    def __init__(self):
        """
        Initialize the document registry service
        初始化文档注册表服务

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

    async def add_document(
        self,
        doc_id: str,
        filename: str,
        chunk_count: int
    ) -> bool:
        """
        Add a document to the registry
        将文档添加到注册表

        Args:
            doc_id: Document ID / 文档 ID
            filename: Original filename / 原始文件名
            chunk_count: Number of chunks / 分块数量
        Returns:
            Whether the operation was successful / 操作是否成功
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).where(DocumentRegistry.id == doc_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.filename = filename
                    existing.chunk_count = chunk_count
                    existing.created_at = datetime.utcnow()
                else:
                    new_doc = DocumentRegistry(
                        id=doc_id,
                        filename=filename,
                        chunk_count=chunk_count,
                        created_at=datetime.utcnow(),
                    )
                    session.add(new_doc)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding document to registry: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return False

    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        Get a document by ID
        根据 ID 获取文档

        Args:
            doc_id: Document ID / 文档 ID
        Returns:
            Document dict or None / 文档字典或 None
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).where(DocumentRegistry.id == doc_id)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    return doc.to_dict()
                return None
        except Exception as e:
            logger.error(f"Error getting document from registry: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return None

    async def list_documents(self) -> List[Dict]:
        """
        List all documents
        列出所有文档

        Returns:
            List of document dicts / 文档字典列表
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).order_by(DocumentRegistry.created_at.desc())
                )
                docs = result.scalars().all()
                return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error listing documents from registry: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the registry
        从注册表中删除文档

        Args:
            doc_id: Document ID to delete / 要删除的文档 ID
        Returns:
            Whether deletion was successful / 删除是否成功
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    delete(DocumentRegistry).where(DocumentRegistry.id == doc_id).returning(DocumentRegistry.id)
                )
                await session.commit()
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error deleting document from registry: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return False


# Global document registry service instance
# 全局文档注册表服务实例
document_registry = DocumentRegistryService()
