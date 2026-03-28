"""
Document management API routes using LangChain text splitters
使用 LangChain 文本分割器的文档管理 API 路由

Day 2 Enhancement: Multi-format document parsing and metadata extraction
Day 2 增强： 多格式文档解析和元数据提取

Day 3 Enhancement: Rebuild BM25 index after document upload/delete
Day 3 增强： 文档上传/删除后重建 BM25 索引

Day 3 Enhancement: Persistent document metadata in PostgreSQL
Day 3 增强： 将文档元数据持久化到 PostgreSQL
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from datetime import datetime

from models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    ApiResponse,
    DocumentMetadata,
    SupportedFormatsResponse,
)
from services.vector_store import vector_store
from services.document_parser import document_parser
from services.retrieval_service import retrieval_service
from services.document_registry import document_registry
from config import settings

# Create router
# 创建路由器
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """
    Get list of supported file formats
    获取支持的文件格式列表

    Day 2: New endpoint to show what file types are supported
    Day 2： 新端点显示支持的文件类型
    """
    return SupportedFormatsResponse(
        extensions=list(document_parser.SUPPORTED_EXTENSIONS.keys()),
        descriptions={
            ".txt": "Plain text file / 纯文本文件",
            ".md": "Markdown document / Markdown 文档",
            ".pdf": "PDF document / PDF 文档",
            ".docx": "Microsoft Word document (2007+) / Microsoft Word 文档 (2007+)",
            ".doc": "Microsoft Word document (legacy) / Microsoft Word 文档（旧版）",
            ".html": "HTML web page / HTML 网页",
            ".htm": "HTML web page / HTML 网页",
        }
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document and process it into chunks
    上传文档并将其处理为分块

    Day 2 Enhancement:
    - Supports multiple file formats (PDF, Word, HTML, Markdown, TXT)
    - Extracts metadata from documents
    - Uses appropriate chunking strategy based on file type

    Day 2 增强:
    - 支持多种文件格式 (PDF, Word, HTML, Markdown, TXT)
    - 从文档中提取元数据
    - 根据文件类型使用适当的分块策略
    """
    # Check if file type is supported
    # 检查文件类型是否支持
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required / 文件名是必需的"
        )

    if not document_parser.is_supported(file.filename):
        supported = ", ".join(document_parser.SUPPORTED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported formats: {supported} "
                   f"不支持的文件类型。 支持的格式: {supported}"
        )

    try:
        # Read file content
        # 读取文件内容
        file_content = await file.read()

        # Parse the document using our parser service
        # 使用解析服务解析文档
        parsed_doc = await document_parser.parse_file(file_content, file.filename)

        if not parsed_doc.chunks:
            raise HTTPException(
                status_code=400,
                detail="Document is empty or could not be parsed. "
                       "文档为空或无法解析。"
            )

        # Store in vector database
        # 存储到向量数据库
        document_id = await vector_store.store_document(
            filename=file.filename,
            chunks=parsed_doc.chunks,
            metadata=parsed_doc.metadata
        )

        # Track document in database registry
        # 在数据库注册表中跟踪文档
        await document_registry.add_document(
            doc_id=document_id,
            filename=file.filename,
            chunk_count=len(parsed_doc.chunks),
            file_type=parsed_doc.document_info.file_type,
            file_size=parsed_doc.document_info.file_size,
            title=parsed_doc.metadata.get("title")
        )

        # Create metadata response
        # 创建元数据响应
        metadata = DocumentMetadata(
            title=parsed_doc.metadata.get("title"),
            file_type=parsed_doc.document_info.file_type,
            file_size=parsed_doc.document_info.file_size,
            extra=parsed_doc.metadata.get("extra"),
        )

        # Day 3: Rebuild BM25 index with new document
        # Day 3： 使用新文档重建 BM25 索引
        try:
            all_docs = await vector_store.get_all_documents_for_bm25()
            if all_docs:
                retrieval_service.build_bm25_index(all_docs)
        except Exception:
            pass  # Non-critical error, continue
                    # 非关键错误，继续

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunk_count=len(parsed_doc.chunks),
            created_at=datetime.now(),
            metadata=metadata,
            file_type=parsed_doc.document_info.file_type,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding error. Please use UTF-8 encoded files. "
                   "文件编码错误。请使用 UTF-8 编码的文件。"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)} "
                   f"处理文档时出错: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    Get list of all uploaded documents
    获取所有已上传文档的列表

    Day 2 Enhancement: Includes file type and size information
    Day 2 增强: 包含文件类型和大小信息

    Day 3 Enhancement: Documents are now persisted in PostgreSQL
    Day 3 增强： 文档现在持久化在 PostgreSQL 中
    """
    try:
        # Get documents from database registry
        # 从数据库注册表获取文档
        docs = await document_registry.list_documents()
        return DocumentListResponse(
            documents=[
                DocumentInfo(
                    id=doc['id'],
                    filename=doc['filename'],
                    chunk_count=doc['chunk_count'],
                    created_at=doc['created_at'],
                    file_type=doc.get('file_type', 'text'),
                    file_size=doc.get('file_size', 0),
                    title=doc.get('title'),
                )
                for doc in docs
            ],
            total=len(docs)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)} "
                   f"列出文档时出错: {str(e)}"
        )


@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(document_id: str):
    """
    Delete a document and its chunks
    删除文档及其分块

    Day 3 Enhancement: Rebuild BM25 index after deletion
    Day 3 增强： 删除后重建 BM25 索引

    Args:
        document_id: ID of document to delete
                     要删除的文档 ID
    Returns:
        Success/failure response
        成功/失败响应
    """
    try:
        success = await vector_store.delete_document(document_id)
        if success:
            # Delete from database registry
            # 从数据库注册表中删除
            await document_registry.delete_document(document_id)

            # Day 3: Rebuild BM25 index after deletion
            # Day 3： 删除后重建 BM25 索引
            try:
                all_docs = await vector_store.get_all_documents_for_bm25()
                if all_docs:
                    retrieval_service.build_bm25_index(all_docs)
            except Exception:
                pass  # Non-critical error, continue
                        # 非关键错误，继续

            return ApiResponse(
                success=True,
                data={"document_id": document_id},
                error=None
            )
        else:
            return ApiResponse(
                success=False,
                data=None,
                error="Document not found / 文档未找到"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)} "
                   f"删除文档时出错: {str(e)}"
        )
