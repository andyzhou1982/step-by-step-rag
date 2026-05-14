"""
Vector store service using LangChain PGVectorStore
使用 LangChain PGVectorStore 的向量存储服务

Day 2 Enhancement: Support for document metadata storage
Day 2 增强： 支持文档元数据存储

Day 3 Enhancement: Added method to retrieve all documents for BM25 indexing
Day 3 增强： 添加了检索所有文档以构建 BM25 索引的方法
"""

import json
import uuid
from langchain_postgres import PGVectorStore
from langchain_postgres.v2.engine import PGEngine
from langchain_core.documents import Document
from config import settings, get_logger
from services.embedding import embedding_service
from typing import List, Tuple, Optional, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = get_logger(__name__)


class VectorStoreService:
    """
    Service for storing and searching vector embeddings using LangChain PGVectorStore
    使用 LangChain PGVectorStore 存储和搜索向量嵌入的服务
    """

    def __init__(self):
        """
        Initialize the vector store service
        初始化向量存储服务
        """
        self._vectorstore: Optional[PGVectorStore] = None
        self._engine: Optional[PGEngine] = None
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        # 将 postgresql:// 转换为 postgresql+asyncpg:// 以支持异步
        self._connection_string = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self._table_name = "rag_documents"
        # Separate async engine for direct SQL queries (BM25 index building)
        # 用于直接 SQL 查询的独立异步引擎（BM25 索引构建）
        self._async_engine = None

    async def connect(self):
        """
        Connect to the database and initialize vector store
        连接数据库并初始化向量存储
        """
        # Create PGEngine
        # 创建 PGEngine
        self._engine = PGEngine.from_connection_string(self._connection_string)

        # Create separate async engine for direct SQL queries
        # 创建独立的异步引擎用于直接 SQL 查询
        self._async_engine = create_async_engine(self._connection_string)

        # Get embedding dimension
        # 获取嵌入维度
        vector_size = len(await embedding_service.embeddings.aembed_query("test"))

        # Initialize table if not exists
        # 如果表不存在则初始化
        async with self._async_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = :table)"),
                {"table": self._table_name}
            )
        if not exists:
            await self._engine.ainit_vectorstore_table(
                table_name=self._table_name,
                vector_size=vector_size,
            )

        # Create PGVectorStore
        # 创建 PGVectorStore
        self._vectorstore = await PGVectorStore.create(
            engine=self._engine,
            embedding_service=embedding_service.embeddings,
            table_name=self._table_name,
        )

    async def disconnect(self):
        """
        Disconnect from the database
        断开数据库连接
        """
        if self._engine:
            await self._engine.close()
        if self._async_engine:
            await self._async_engine.dispose()
        self._vectorstore = None
        self._engine = None
        self._async_engine = None

    @property
    def vectorstore(self) -> PGVectorStore:
        """
        Get the vector store instance
        获取向量存储实例
        """
        if self._vectorstore is None:
            raise RuntimeError("Vector store not connected. Call connect() first.")
        return self._vectorstore

    async def store_document(
        self,
        filename: str,
        chunks: List[str],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store a document and its chunks with embeddings
        存储文档及其带有嵌入的分块

        Day 2 Enhancement: Added metadata parameter
        Day 2 增强： 添加了元数据参数

        Args:
            filename: Original filename
                      原始文件名
            chunks: List of text chunks
                    文本分块列表
            metadata: Optional document metadata
                      可选的文档元数据
        Returns:
            Document ID
            文档 ID
        """
        # Merge metadata with default values
        # 将元数据与默认值合并
        doc_metadata = metadata or {}

        # Generate a unique document ID for grouping all chunks
        # 生成唯一的文档 ID 用于分组所有分块
        # Fix: Use doc_id instead of PGVector's first chunk ID for reliable deletion
        # 修复：使用 doc_id 而非 PGVector 的第一个 chunk ID，确保删除操作可靠
        doc_id = str(uuid.uuid4())

        # Create Document objects with metadata
        # 创建带有元数据的 Document 对象
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "file_type": doc_metadata.get("file_type", "text"),
                    "title": doc_metadata.get("title"),
                    "file_size": doc_metadata.get("file_size", 0),
                }
            )
            for i, chunk in enumerate(chunks)
        ]

        # Add documents to vector store
        # 将文档添加到向量存储
        await self.vectorstore.aadd_documents(documents)

        # Return the generated doc_id as document identifier
        # 返回生成的 doc_id 作为文档标识符
        return doc_id

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        file_types: Optional[List[str]] = None
    ) -> List[Tuple[str, str, str, str, float, str]]:
        """
        Search for similar chunks using vector similarity
        使用向量相似度搜索相似分块

        Day 2 Enhancement: Added file_types filter
        Day 2 增强： 添加了 file_types 过滤器

        Args:
            query: Search query
                   搜索查询
            top_k: Number of results to return
                   返回的结果数量
            file_types: Optional filter by file types
                        可选的按文件类型过滤
        Returns:
            List of (chunk_id, document_id, content, filename, score, file_type)
            (分块ID, 文档ID, 内容, 文件名, 分数, 文件类型) 列表
        """
        # Build filter if file_types specified
        # 如果指定了 file_types 则构建过滤器
        search_kwargs = {"k": top_k}
        if file_types:
            # Note: PGVector filter syntax
            # 注意：PGVector 过滤语法
            search_kwargs["filter"] = {"file_type": {"$in": file_types}}

        # Perform similarity search with scores
        # 执行带分数的相似度搜索
        results = await self.vectorstore.asimilarity_search_with_score(
            query, **search_kwargs
        )

        # Format results
        # 格式化结果
        formatted_results = []
        for doc, score in results:
            chunk_id = doc.id or ""
            doc_id = doc.metadata.get("source", chunk_id)
            filename = doc.metadata.get("filename", "unknown")
            content = doc.page_content
            file_type = doc.metadata.get("file_type", "text")
            # Convert distance to similarity score (1 - distance)
            # 将距离转换为相似度分数（1 - 距离）
            similarity = 1 - score if score <= 1 else score
            formatted_results.append((
                chunk_id,
                doc_id,
                content,
                filename,
                round(similarity, 4),
                file_type
            ))

        return formatted_results

    async def get_documents(self) -> List[dict]:
        """
        Get list of all documents
        获取所有文档列表

        Returns:
            List of document info dicts
            文档信息字典列表
        """
        # Note: PGVector doesn't have a direct method for this
        # 注意：PGVector 没有直接的方法来实现这个
        # This returns empty list, actual tracking is in document_registry
        # 这返回空列表，实际跟踪在 document_registry 中
        return []

    async def get_all_documents_for_bm25(self) -> List[Dict]:
        """
        Get all documents for BM25 indexing
        获取所有文档用于 BM25 索引

        Day 3: Added to support BM25 index building
        Day 3： 添加以支持 BM25 索引构建

        Returns:
            List of document dicts with content and metadata
            包含内容和元数据的文档字典列表
        """
        # Use direct SQL query to get all documents
        # 使用直接 SQL 查询获取所有文档
        if not self._async_engine:
            return []

        try:
            # Use separate async engine to avoid event loop conflicts
            # 使用独立的异步引擎以避免事件循环冲突
            async with self._async_engine.connect() as conn:
                # Query all documents from the table
                # 从表中查询所有文档
                result = await conn.execute(
                    text(f"SELECT langchain_id, content, langchain_metadata FROM {self._table_name}")
                )
                rows = result.fetchall()

                documents = []
                for row in rows:
                    # Parse metadata if it's a string
                    # 如果元数据是字符串则解析
                    metadata = row.langchain_metadata if hasattr(row, 'langchain_metadata') else {}
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}

                    documents.append({
                        "chunk_id": str(row.langchain_id) or "",
                        "document_id": metadata.get("source", ""),
                        "content": row.content or "",
                        "filename": metadata.get("filename", "unknown"),
                        "file_type": metadata.get("file_type", "text"),
                    })
                return documents
        except Exception as e:
            logger.warning(f"Failed to get documents for BM25: {e}", exc_info=True)
            return []

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its chunks
        删除文档及其分块

        Args:
            document_id: Document ID to delete
                         要删除的文档 ID
        Returns:
            Whether deletion was successful
            删除是否成功
        """
        # Note: PGVector delete by filter on doc_id metadata
        # 注意：PGVector 按 doc_id 元数据过滤删除
        # Fix: Use doc_id filter instead of filename to match the generated UUID
        # 修复：使用 doc_id 过滤器而非 filename，匹配生成的 UUID
        try:
            await self.vectorstore.adelete(
                filter={"doc_id": document_id}
            )
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        """
        Check if vector store connection is alive
        检查向量存储连接是否存活
        """
        return self._vectorstore is not None


# Global vector store service instance
# 全局向量存储服务实例
vector_store = VectorStoreService()
