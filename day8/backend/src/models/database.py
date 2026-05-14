"""
Unified database models for all tables
所有表的统一数据库模型

Day 6 Enhancement: SQLAlchemy ORM for all data storage
Day 6 增强： 所有数据存储使用 SQLAlchemy ORM

Day 8 Enhancement: Added Wiki page models for knowledge compilation
Day 8 增强： 添加了 Wiki 页面模型用于知识编译

Tables:
- app_users: User management
- audit_logs: Audit logging
- document_registry: Document tracking (replaces JSON file)
- wiki_pages: Wiki knowledge pages
- wiki_links: Cross-references between wiki pages
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Index, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
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

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
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


class WikiPage(Base):
    """
    Wiki page model for knowledge compilation
    用于知识编译的 Wiki 页面模型

    Day 8: LLM reads documents → extracts concepts → generates structured Wiki pages
    Day 8： LLM 阅读文档 → 提取概念 → 生成结构化 Wiki 页面
    """
    __tablename__ = "wiki_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Wiki page title (concept name)
    # Wiki 页面标题（概念名称）
    title = Column(String(500), nullable=False, index=True)
    # Wiki page content in markdown format
    # Markdown 格式的 Wiki 页面内容
    content = Column(Text, nullable=False)
    # Summary of the page (first few sentences)
    # 页面摘要（前几句话）
    summary = Column(Text, nullable=True)
    # Concepts/tags extracted from source documents
    # 从源文档中提取的概念/标签
    concepts = Column(JSONB, nullable=False, default=list)
    # Source document IDs that contributed to this page
    # 贡献于此页面的源文档 ID
    source_document_ids = Column(JSONB, nullable=False, default=list)
    # Source chunk IDs for traceability
    # 用于追溯的源分块 ID
    source_chunk_ids = Column(JSONB, nullable=False, default=list)
    # Version number for tracking updates
    # 用于跟踪更新的版本号
    version = Column(Integer, nullable=False, default=1)
    # Embedding vector stored separately via pgvector
    # 通过 pgvector 单独存储的嵌入向量
    # (handled by vector_store for semantic search)
    # （由 vector_store 处理语义搜索）
    embedding_id = Column(String(255), nullable=True)
    # Confidence score of the generated content
    # 生成内容的置信度评分
    confidence = Column(Float, nullable=False, default=0.0)
    # Generation metadata (LLM model used, token count, etc.)
    # 生成元数据（使用的 LLM 模型、token 数等）
    generation_meta = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_wiki_pages_title', 'title'),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "concepts": self.concepts or [],
            "source_document_ids": [str(did) for did in (self.source_document_ids or [])],
            "source_chunk_ids": self.source_chunk_ids or [],
            "version": self.version,
            "confidence": self.confidence,
            "generation_meta": self.generation_meta or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WikiLink(Base):
    """
    Cross-reference links between Wiki pages
    Wiki 页面之间的交叉引用链接

    Day 8: Tracks concept relationships between Wiki pages
    Day 8： 跟踪 Wiki 页面之间的概念关系
    """
    __tablename__ = "wiki_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Source wiki page
    # 源 Wiki 页面
    source_page_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Target wiki page
    # 目标 Wiki 页面
    target_page_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    # Relationship type (e.g., "related_to", "depends_on", "part_of")
    # 关系类型（如 "related_to"、"depends_on"、"part_of"）
    relation_type = Column(String(100), nullable=False, default="related_to")
    # Confidence of this relationship
    # 此关系的置信度
    confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_wiki_links_source', 'source_page_id'),
        Index('idx_wiki_links_target', 'target_page_id'),
    )

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return {
            "id": str(self.id),
            "source_page_id": str(self.source_page_id),
            "target_page_id": str(self.target_page_id),
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
