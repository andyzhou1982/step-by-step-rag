"""
Document management API routes using LangChain text splitters
使用 LangChain 文本分割器的文档管理 API 路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from datetime import datetime

from models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    ApiResponse
)
from services.vector_store import vector_store
from config import settings

# Create router
# 创建路由器
router = APIRouter(prefix="/documents", tags=["Documents"])

# In-memory document tracking (Day 1 only)
# 内存文档跟踪（仅 Day 1）
document_registry: dict = {}


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Get a LangChain text splitter instance
    获取 LangChain 文本分割器实例
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document and process it into chunks using LangChain
    使用 LangChain 上传文档并将其处理为分块

    Args:
        file: Uploaded file (currently supports .txt files)
              上传的文件（目前支持 .txt 文件）
    Returns:
        Document upload response with ID and chunk count
        包含 ID 和分块数量的文档上传响应
    """
    # Check file type
    # 检查文件类型
    if not file.filename or not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported in Day 1. "
                   "Day 1 仅支持 .txt 文件。"
        )

    try:
        # Read file content
        # 读取文件内容
        content = await file.read()
        text = content.decode('utf-8')

        # Split text using LangChain text splitter
        # 使用 LangChain 文本分割器分割文本
        splitter = get_text_splitter()
        chunks = splitter.split_text(text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Document is empty or could not be parsed. "
                       "文档为空或无法解析。"
            )

        # Store in vector database
        # 存储到向量数据库
        document_id = await vector_store.store_document(
            filename=file.filename,
            chunks=chunks
        )

        # Track document in registry
        # 在注册表中跟踪文档
        document_registry[document_id] = {
            "id": document_id,
            "filename": file.filename,
            "chunk_count": len(chunks),
            "created_at": datetime.now(),
        }

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunk_count=len(chunks),
            created_at=datetime.now()
        )

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

    Returns:
        List of documents with metadata
        带有元数据的文档列表
    """
    try:
        # Return from registry (Day 1 uses in-memory storage)
        # 从注册表返回（Day 1 使用内存存储）
        docs = list(document_registry.values())
        return DocumentListResponse(
            documents=[
                DocumentInfo(
                    id=doc['id'],
                    filename=doc['filename'],
                    chunk_count=doc['chunk_count'],
                    created_at=doc['created_at']
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

    Args:
        document_id: ID of document to delete
                     要删除的文档 ID
    Returns:
        Success/failure response
        成功/失败响应
    """
    try:
        success = await vector_store.delete_document(document_id)
        if success and document_id in document_registry:
            del document_registry[document_id]
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
