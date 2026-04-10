"""
Database models for Day 2-4 tables
Day 2-4 数据库模型

Uses SQLAlchemy ORM for database operations
使用 SQLAlchemy ORM 进行数据库操作
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, BigInteger
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models / 所有数据库模型的基类"""
    pass


class DocumentRegistry(Base):
    """
    Document registry for tracking uploaded documents
    用于跟踪上传文档的注册表
    """
    __tablename__ = "document_registry"

    id = Column(String(255), primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    chunk_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    file_type = Column(String(100))
    file_size = Column(BigInteger)
    title = Column(String(500))

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": self.id,
            "filename": self.filename,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
            "file_type": self.file_type or "text",
            "file_size": self.file_size or 0,
            "title": self.title,
        }
