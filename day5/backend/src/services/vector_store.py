"""
Vector store service using LangChain PGVector
使用 LangChain PGVector 的向量存储服务

Day 2 Enhancement: Support for document metadata storage
Day 2 增强： 支持文档元数据存储

Day 3 Enhancement: Added method to retrieve all documents for BM25 indexing
Day 3 增强： 添加了检索所有文档以构建 BM25 索引的方法
"""

from langchain_postgres import PGVector
from langchain_core.documents import Document
from config import settings
from services.embedding import embedding_service
from typing import List, Tuple, Optional, Dict


class VectorStoreService:
    """
    Service for storing and searching vector embeddings using LangChain PGVector
    使用 LangChain PGVector 存储和搜索向量嵌入的服务
    """

    def __init__(self):
        """
        Initialize the vector store service
        初始化向量存储服务
        """
        self._vectorstore: Optional[PGVector] = None
        self._connection_string = settings.database_url

    async def connect(self):
        """
        Connect to the database and initialize vector store
        连接数据库并初始化向量存储
        """
        # Create PGVector vectorstore
        # 创建 PGVector 向量存储
        self._vectorstore = PGVector(
            embeddings=embedding_service.embeddings,
            connection=self._connection_string,
            collection_name="rag_documents",
            use_jsonb=True,
        )

    async def disconnect(self):
        """
        Disconnect from the database
        断开数据库连接
        """
        # PGVector handles connection pooling internally
        # PGVector 内部处理连接池
        self._vectorstore = None

    @property
    def vectorstore(self) -> PGVector:
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

        # Create Document objects with metadata
        # 创建带有元数据的 Document 对象
        documents = [
            Document(
                page_content=chunk,
                metadata={
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
        ids = await self.vectorstore.aadd_documents(documents)

        # Return first ID as document identifier
        # 返回第一个 ID 作为文档标识符
        return ids[0] if ids else ""

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
        # Use vector store to get all documents
        # 使用向量存储获取所有文档
        try:
            # Perform a broad search to get all documents
            # 执行广泛搜索以获取所有文档
            results = await self.vectorstore.asimilarity_search(
                "",  # Empty query to match all
                k=1000  # Large number to get all
            )
            documents = []
            for doc in results:
                documents.append({
                    "chunk_id": doc.id or "",
                    "document_id": doc.metadata.get("source", ""),
                    "content": doc.page_content,
                    "filename": doc.metadata.get("filename", "unknown"),
                    "file_type": doc.metadata.get("file_type", "text"),
                })
            return documents
        except Exception:
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
        # Note: PGVector delete by filter
        # 注意：PGVector 按过滤器删除
        try:
            await self.vectorstore.adelete(
                filter={"filename": document_id}
            )
            return True
        except Exception:
            return False


# Global vector store service instance
# 全局向量存储服务实例
vector_store = VectorStoreService()
