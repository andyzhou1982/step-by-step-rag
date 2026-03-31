"""
Document registry service for persistent document metadata storage
文档注册表服务，用于持久化文档元数据存储

Day 3 Enhancement: Store document metadata in PostgreSQL instead of memory
Day 3 增强： 将文档元数据存储在 PostgreSQL 中而不是内存中
"""

import traceback
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings, get_logger

# Get logger for this module
# 获取此模块的日志记录器
logger = get_logger(__name__)


class DocumentRegistryService:
    """
    Service for managing document metadata in PostgreSQL
    在 PostgreSQL 中管理文档元数据的服务
    """

    def __init__(self):
        """
        Initialize the document registry service
        初始化文档注册表服务
        """
        self._connection_string = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self._async_engine = None
        self._table_name = "document_registry"

    async def connect(self):
        """
        Connect to the database and initialize the registry table
        连接数据库并初始化注册表
        """
        self._async_engine = create_async_engine(self._connection_string)

        # Create table if not exists
        # 如果表不存在则创建
        async with self._async_engine.connect() as conn:
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id VARCHAR(255) PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    file_type VARCHAR(100),
                    file_size BIGINT,
                    title VARCHAR(500)
                )
            """))
            await conn.commit()

    async def disconnect(self):
        """
        Disconnect from the database
        断开数据库连接
        """
        if self._async_engine:
            await self._async_engine.dispose()
        self._async_engine = None

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
            async with self._async_engine.connect() as conn:
                await conn.execute(text(f"""
                    INSERT INTO {self._table_name}
                    (id, filename, chunk_count, created_at, file_type, file_size, title)
                    VALUES (:id, :filename, :chunk_count, :created_at, :file_type, :file_size, :title)
                    ON CONFLICT (id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        chunk_count = EXCLUDED.chunk_count,
                        file_type = EXCLUDED.file_type,
                        file_size = EXCLUDED.file_size,
                        title = EXCLUDED.title
                """), {
                    "id": doc_id,
                    "filename": filename,
                    "chunk_count": chunk_count,
                    "created_at": datetime.now(),
                    "file_type": file_type,
                    "file_size": file_size,
                    "title": title
                })
                await conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding document to registry: {e}")
            logger.debug(f"Add document error traceback:\n{traceback.format_exc()}")
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
            async with self._async_engine.connect() as conn:
                result = await conn.execute(text(f"""
                    SELECT id, filename, chunk_count, created_at, file_type, file_size, title
                    FROM {self._table_name}
                    WHERE id = :id
                """), {"id": doc_id})
                row = result.fetchone()
                if row:
                    return {
                        "id": row.id,
                        "filename": row.filename,
                        "chunk_count": row.chunk_count,
                        "created_at": row.created_at,
                        "file_type": row.file_type or "text",
                        "file_size": row.file_size or 0,
                        "title": row.title
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting document from registry: {e}")
            logger.debug(f"Get document error traceback:\n{traceback.format_exc()}")
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
            async with self._async_engine.connect() as conn:
                result = await conn.execute(text(f"""
                    SELECT id, filename, chunk_count, created_at, file_type, file_size, title
                    FROM {self._table_name}
                    ORDER BY created_at DESC
                """))
                rows = result.fetchall()
                return [
                    {
                        "id": row.id,
                        "filename": row.filename,
                        "chunk_count": row.chunk_count,
                        "created_at": row.created_at,
                        "file_type": row.file_type or "text",
                        "file_size": row.file_size or 0,
                        "title": row.title
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error listing documents from registry: {e}")
            logger.debug(f"List documents error traceback:\n{traceback.format_exc()}")
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
            async with self._async_engine.connect() as conn:
                result = await conn.execute(text(f"""
                    DELETE FROM {self._table_name}
                    WHERE id = :id
                    RETURNING id
                """), {"id": doc_id})
                await conn.commit()
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error deleting document from registry: {e}")
            logger.debug(f"Delete document error traceback:\n{traceback.format_exc()}")
            return False


# Global document registry service instance
# 全局文档注册表服务实例
document_registry = DocumentRegistryService()
