"""
Document registry service for persistent document metadata storage
文档注册表服务，用于持久化文档元数据存储

Day 3 Enhancement: Store document metadata in PostgreSQL instead of memory
Day 3 增强： 将文档元数据存储在 PostgreSQL 中而不是内存中

Day 6 Enhancement: Now uses SQLAlchemy ORM instead of raw SQL
Day 6 增强： 现在使用 SQLAlchemy ORM 替代原始 SQL
"""

from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings, get_logger
from models.database import DocumentRegistry
from services.database_service import db_service

logger = get_logger(__name__)


class DocumentRegistryService:
    """
    Service for managing document metadata in PostgreSQL
    在 PostgreSQL 中管理文档元数据的服务

    Day 6 Enhancement: Uses SQLAlchemy ORM for database operations
    Day 6 增强： 使用 SQLAlchemy ORM 进行数据库操作
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
        chunk_count: int,
        file_type: str = "text",
        file_size: int = 0,
        title: Optional[str] = None
    ) -> bool:
        """
        Add a document to the registry
        将文档添加到注册表

        Args:
            doc_id: Document ID
                    文档 ID
            filename: Original filename
                      原始文件名
            chunk_count: Number of chunks
                         分块数量
            file_type: File type
                       文件类型
            file_size: File size in bytes
                       文件大小（字节）
            title: Document title
                   文档标题
        Returns:
            Whether the operation was successful
            操作是否成功
        """
        try:
            async with db_service.session_factory() as session:
                # Check if document already exists
                # 检查文档是否已存在
                result = await session.execute(
                    select(DocumentRegistry).where(DocumentRegistry.filename == filename)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing document
                    # 更新现有文档
                    existing.file_type = file_type
                    existing.file_size = file_size
                    existing.chunk_count = chunk_count
                    existing.created_at = datetime.utcnow()
                else:
                    # Create new document registry entry
                    # 创建新的文档注册条目
                    new_doc = DocumentRegistry(
                        filename=filename,
                        file_type=file_type,
                        file_size=file_size,
                        created_at=datetime.utcnow(),
                        chunk_count=chunk_count,
                    )
                    session.add(new_doc)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding document to registry: {e}", exc_info=True)
            return False

    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        Get a document by ID
        根据 ID 获取文档

        Args:
            doc_id: Document ID
                    文档 ID
        Returns:
            Document dict or None
            文档字典或 None
        """
        try:
            import uuid
            doc_uuid = uuid.UUID(doc_id)
        except ValueError:
            return None

        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).where(DocumentRegistry.id == doc_uuid)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    return doc.to_dict()
                return None
        except Exception as e:
            logger.error(f"Error getting document from registry: {e}", exc_info=True)
            return None

    async def get_document_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Get a document by filename
        根据文件名获取文档

        Args:
            filename: Document filename
                      文档文件名
        Returns:
            Document dict or None
            文档字典或 None
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).where(DocumentRegistry.filename == filename)
                )
                doc = result.scalar_one_or_none()

                if doc:
                    return doc.to_dict()
                return None
        except Exception as e:
            logger.error(f"Error getting document from registry: {e}", exc_info=True)
            return None

    async def list_documents(self) -> List[Dict]:
        """
        List all documents
        列出所有文档

        Returns:
            List of document dicts
            文档字典列表
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    select(DocumentRegistry).order_by(DocumentRegistry.created_at.desc())
                )
                docs = result.scalars().all()
                return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error listing documents from registry: {e}", exc_info=True)
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the registry
        从注册表中删除文档

        Args:
            doc_id: Document ID to delete
                    要删除的文档 ID
        Returns:
            Whether deletion was successful
            删除是否成功
        """
        try:
            import uuid
            doc_uuid = uuid.UUID(doc_id)
        except ValueError:
            return False

        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    delete(DocumentRegistry).where(DocumentRegistry.id == doc_uuid).returning(DocumentRegistry.id)
                )
                await session.commit()
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error deleting document from registry: {e}", exc_info=True)
            return False

    async def delete_document_by_filename(self, filename: str) -> bool:
        """
        Delete a document from the registry by filename
        根据文件名从注册表中删除文档

        Args:
            filename: Document filename to delete
                      要删除的文档文件名
        Returns:
            Whether deletion was successful
            删除是否成功
        """
        try:
            async with db_service.session_factory() as session:
                result = await session.execute(
                    delete(DocumentRegistry).where(DocumentRegistry.filename == filename).returning(DocumentRegistry.id)
                )
                await session.commit()
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error deleting document from registry: {e}", exc_info=True)
            return False


# Global document registry service instance
# 全局文档注册表服务实例
document_registry = DocumentRegistryService()
