"""
Vector store service using LangChain PGVectorStore
使用 LangChain PGVectorStore 的向量存储服务
"""

from langchain_postgres import PGVectorStore
from langchain_postgres.v2.engine import PGEngine
from langchain_core.documents import Document
from config import settings
from services.embedding import embedding_service
from typing import List, Tuple, Optional
from sqlalchemy.exc import ProgrammingError


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

    async def connect(self):
        """
        Connect to the database and initialize vector store
        连接数据库并初始化向量存储
        """
        # Create PGEngine
        # 创建 PGEngine
        self._engine = PGEngine.from_connection_string(self._connection_string)

        # Get embedding dimension
        # 获取嵌入维度
        vector_size = len(await embedding_service.embeddings.aembed_query("test"))

        # Initialize table if not exists
        # 如果表不存在则初始化
        try:
            await self._engine.ainit_vectorstore_table(
                table_name=self._table_name,
                vector_size=vector_size,
            )
        except ProgrammingError:
            # Table already exists, which is fine
            # 表已存在，无需处理
            pass

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
        self._vectorstore = None
        self._engine = None

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
        chunks: List[str]
    ) -> str:
        """
        Store a document and its chunks with embeddings
        存储文档及其带有嵌入的分块

        Args:
            filename: Original filename
                      原始文件名
            chunks: List of text chunks
                    文本分块列表
        Returns:
            Document ID
            文档 ID
        """
        # Create Document objects with metadata
        # 创建带有元数据的 Document 对象
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "filename": filename,
                    "chunk_index": i,
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
        top_k: int = 5
    ) -> List[Tuple[str, str, str, str, float]]:
        """
        Search for similar chunks using vector similarity
        使用向量相似度搜索相似分块

        Args:
            query: Search query
                   搜索查询
            top_k: Number of results to return
                   返回的结果数量
        Returns:
            List of (chunk_id, document_id, content, filename, score)
            (分块ID, 文档ID, 内容, 文件名, 分数) 列表
        """
        # Perform similarity search with scores
        # 执行带分数的相似度搜索
        results = await self.vectorstore.asimilarity_search_with_score(
            query, k=top_k
        )

        # Format results
        # 格式化结果
        formatted_results = []
        for doc, score in results:
            chunk_id = doc.id or ""
            doc_id = doc.metadata.get("source", chunk_id)
            filename = doc.metadata.get("filename", "unknown")
            content = doc.page_content
            # Convert distance to similarity score (1 - distance)
            # 将距离转换为相似度分数（1 - 距离）
            similarity = 1 - score if score <= 1 else score
            formatted_results.append((
                chunk_id,
                doc_id,
                content,
                filename,
                round(similarity, 4)
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
        # We'll implement a simplified version for Day 1
        # 注意：PGVector 没有直接的方法来实现这个
        # 我们将在 Day 1 实现一个简化版本
        # This will be enhanced in Day 2
        # 这将在 Day 2 中增强
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
