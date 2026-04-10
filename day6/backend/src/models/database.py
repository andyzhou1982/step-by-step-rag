"""
Unified database models for all tables
所有表的统一数据库模型

Day 6 Enhancement: SQLAlchemy ORM for all data storage
Day 6 增强： 所有数据存储使用 SQLAlchemy ORM

Tables:
- app_users: User management
- audit_logs: Audit logging
- document_registry: Document tracking (replaces JSON file)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
import uuid


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models / 所有数据库模型的基类"""
    pass


class AppUser(Base):
    """
    User model for authentication and authorization
    用于认证和授权的用户模型
    """
    __tablename__ = "app_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary (without password) / 转换为字典（不含密码）"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class AuditLog(Base):
    """
    Audit log model for tracking user actions
    用于跟踪用户操作的审计日志模型
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action = Column(String(50), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    details = Column(JSONB, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="success", index=True)
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "user_id": str(self.user_id),
            "username": self.username,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
        }


class DocumentRegistry(Base):
    """
    Document registry for tracking uploaded documents
    用于跟踪上传文档的注册表

    Replaces the JSON file-based document registry
    替代基于 JSON 文件的文档注册表
    """
    __tablename__ = "document_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    chunk_count = Column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chunk_count": self.chunk_count,
        }


class QAHistory(Base):
    """
    QA history for storing question-answer records
    用于存储问答记录的问答历史

    Day 5 Enhancement: Persistent QA history for evaluation
    Day 5 增强： 持久化问答历史用于评估

    Day 6 Enhancement: Now uses SQLAlchemy ORM
    Day 6 增强： 现在使用 SQLAlchemy ORM
    """
    __tablename__ = "qa_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    contexts = Column(JSONB, nullable=False, default=list)
    sources = Column(JSONB, nullable=False, default=dict)
    retrieval_method = Column(String(50), nullable=True)
    confidence = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": str(self.id),
            "question": self.question,
            "answer": self.answer,
            "contexts": self.contexts or [],
            "sources": self.sources or {},
            "retrieval_method": self.retrieval_method,
            "confidence": float(self.confidence or 0) / 100.0 if self.confidence else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
        }
