# Day 2 核心修改文档 / Day 2 Core Changes Documentation

本文档列出了 Day 2 相对于 Day 1 的核心修改及其原因。
This document lists the core changes from Day 1 to Day 2 and the reasons behind them.

---

## 1. 新增文件 / New Files

### `backend/src/services/document_parser.py`

**功能 / Purpose:**
多格式文档解析服务，支持 PDF、Word、HTML、Markdown 和纯文本。

**为什么新增 / Why Added:**
- Day 1 仅支持 `.txt` 文件
- Day 2 需要支持企业常见的文档格式
- 统一解析接口，便于后续扩展

**核心类 / Core Classes:**
```python
class DocumentParserService:
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx', '.doc', '.html', '.htm'}

    async def parse_file(file_content, filename) -> ParsedDocument
```

**解析策略 / Parsing Strategies:**
| 格式 | 解析库 | 分块策略 |
|------|--------|----------|
| `.txt` | 内置 | RecursiveCharacterTextSplitter |
| `.md` | 内置 | MarkdownHeaderTextSplitter |
| `.pdf` | PyPDF | RecursiveCharacterTextSplitter |
| `.docx` | python-docx | RecursiveCharacterTextSplitter |
| `.html` | BeautifulSoup | HTMLHeaderTextSplitter |

---

## 2. 修改的文件 / Modified Files

### `backend/pyproject.toml`

**修改内容 / Changes:**
```diff
+ # Document Parsers (Day 2 additions)
+ "pypdf>=5.0.0",
+ "python-docx>=1.1.0",
+ "beautifulsoup4>=4.12.0",
+ "lxml>=5.0.0",
+ "chardet>=5.2.0",
```

**原因 / Reason:**
- 添加 PDF 解析支持 (pypdf)
- 添加 Word 文档支持 (python-docx)
- 添加 HTML 解析支持 (beautifulsoup4, lxml)
- 添加编码自动检测 (chardet)

---

### `backend/src/models/schemas.py`

**修改内容 / Changes:**

#### 新增模型 / New Models:

```python
class DocumentMetadata(BaseModel):
    """文档元数据 / Document metadata"""
    title: Optional[str] = None
    file_type: str
    file_size: int
    extra: Optional[Dict] = None

class SupportedFormatsResponse(BaseModel):
    """支持的格式响应 / Supported formats response"""
    extensions: List[str]
    descriptions: Dict[str, str]
```

#### 修改的模型 / Modified Models:

```python
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    created_at: datetime
+   metadata: Optional[DocumentMetadata] = None  # Day 2 新增
+   file_type: str = "text"                     # Day 2 新增

class DocumentInfo(BaseModel):
    # ... existing fields ...
+   file_type: str = "text"      # Day 2 新增
+   file_size: int = 0           # Day 2 新增
+   title: Optional[str] = None  # Day 2 新增

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int
+   supported_types: List[str] = [...]  # Day 2 新增

class SourceReference(BaseModel):
    # ... existing fields ...
+   file_type: str = "text"  # Day 2 新增

class HealthResponse(BaseModel):
    # ... existing fields ...
+   day: int = 2  # Day 2 新增
```

**原因 / Reason:**
- 支持存储和展示文档元数据
- 允许客户端查询支持的文件格式
- 增强来源引用信息

---

### `backend/src/routers/documents.py`

**修改内容 / Changes:**

#### 新增端点 / New Endpoint:

```python
@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """返回支持的文件格式列表"""
```

#### 修改的上传端点 / Modified Upload Endpoint:

```python
@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
-   # Day 1: Only check .txt extension
-   if not file.filename.endswith('.txt'):
-       raise HTTPException(...)
+   # Day 2: Use document parser service
+   if not document_parser.is_supported(file.filename):
+       raise HTTPException(...)

-   # Day 1: Manual text splitting
-   text = content.decode('utf-8')
-   chunks = splitter.split_text(text)
+   # Day 2: Use document parser
+   parsed_doc = await document_parser.parse_file(file_content, file.filename)
```

**原因 / Reason:**
- 委托解析逻辑给专门的服务
- 支持多种文件格式
- 统一的错误处理

---

### `backend/src/services/vector_store.py`

**修改内容 / Changes:**

```python
async def store_document(
    self,
    filename: str,
    chunks: List[str],
+   metadata: Optional[Dict] = None  # Day 2 新增
) -> str:
    # Day 2: 将元数据合并到每个文档块
    doc_metadata = metadata or {}
    documents = [
        Document(
            page_content=chunk,
            metadata={
                "filename": filename,
                "chunk_index": i,
+               "file_type": doc_metadata.get("file_type", "text"),
+               "title": doc_metadata.get("title"),
+               "file_size": doc_metadata.get("file_size", 0),
            }
        )
        ...
    ]

async def search_similar(
    self,
    query: str,
    top_k: int = 5,
+   file_types: Optional[List[str]] = None  # Day 2 新增
- ) -> List[Tuple[str, str, str, str, float]]:
+ ) -> List[Tuple[str, str, str, str, float, str]]:  # 新增 file_type
```

**原因 / Reason:**
- 存储文档元数据用于过滤和展示
- 支持按文件类型过滤搜索结果
- 返回文件类型信息供前端展示

---

### `backend/src/routers/chat.py`

**修改内容 / Changes:**

```python
@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    # Day 2: 支持文件类型过滤
    search_results = await vector_store.search_similar(
        query=request.question,
        top_k=settings.top_k,
+       file_types=request.file_types if hasattr(request, 'file_types') else None
    )

    # Day 2: 解包 6 个值（新增 file_type）
-   for chunk_id, doc_id, content, filename, score in search_results:
+   for result in search_results:
+       if len(result) == 6:
+           chunk_id, doc_id, content, filename, score, file_type = result
```

**原因 / Reason:**
- 支持 ChatRequest 中的 file_types 过滤
- 正确处理新增的 file_type 字段

---

### `backend/src/main.py`

**修改内容 / Changes:**

```python
app = FastAPI(
    title="Step-by-Step RAG API",
-   version="1.0.0",
+   version="2.0.0",
    description="""
-   ## Day 1: Minimal RAG Implementation
+   ## Day 2: Enhanced Document Processing
+
+   ### Day 2 Features:
+   - Multi-format support: PDF, Word, HTML, Markdown, TXT
+   - Metadata extraction: Title, file type, size
+   - Smart chunking: Format-aware text splitting
    """,
)

@app.get("/")
async def root():
    return {
-       "version": "1.0.0",
-       "day": 1,
+       "version": "2.0.0",
+       "day": 2,
+       "features": ["multi-format", "metadata", "smart-chunking"],
    }
```

**原因 / Reason:**
- 更新版本号和描述以反映 Day 2 功能
- 更新根端点响应

---

## 3. 依赖变更 / Dependency Changes

### 新增依赖 / Added Dependencies:

| 包 | 版本 | 用途 |
|----|------|------|
| `pypdf` | >=5.0.0 | PDF 文档解析 |
| `python-docx` | >=1.1.0 | Word 文档解析 |
| `beautifulsoup4` | >=4.12.0 | HTML 解析 |
| `lxml` | >=5.0.0 | XML/HTML 后端 |
| `chardet` | >=5.2.0 | 编码检测 |

---

## 4. API 变更 / API Changes

### 新增端点 / New Endpoints:

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/documents/formats` | 获取支持的文件格式 |

### 修改的响应 / Modified Responses:

**DocumentUploadResponse:**
```json
{
  "document_id": "xxx",
  "filename": "document.pdf",
  "chunk_count": 10,
  "created_at": "2025-03-22T...",
+ "metadata": {
+   "title": "Document Title",
+   "file_type": "pdf",
+   "file_size": 102400
+ },
+ "file_type": "pdf"
}
```

**SourceReference:**
```json
{
  "document_id": "xxx",
  "filename": "document.pdf",
  "content": "...",
  "score": 0.85,
+ "file_type": "pdf"
}
```

---

## 5. 设计决策 / Design Decisions

### 为什么使用独立的 DocumentParserService？

1. **单一职责原则**: 解析逻辑与存储逻辑分离
2. **可测试性**: 可以独立测试解析功能
3. **可扩展性**: 添加新格式只需修改一个文件

### 为什么保留内存文档注册表？

- Day 6 将添加完整的数据库存储
- Day 2 专注于文档处理能力

### 为什么使用 chardet？

- 处理非 UTF-8 编码的文件
- 提高文件解析成功率

---

## 6. 数据库迁移增强 / Database Migration Enhancement (Post-Release Update)

### 概述 / Overview

Day 2 已完成从原始 SQL 到 SQLAlchemy ORM 的迁移，与 Day 6+ 统一数据库存储方式。

### 新增文件 / New Files

- `backend/src/models/database.py` - ORM 模型定义（DocumentRegistry: id=String(255), filename, chunk_count, created_at, file_type, file_size, title）
- `backend/src/services/database_service.py` - 统一数据库连接和会话管理（create_async_engine + async_sessionmaker）

### 修改文件 / Modified Files

- `backend/src/services/document_registry.py` - 原始 SQL → SQLAlchemy ORM，不再自管 `_async_engine`
- `backend/src/main.py` - 添加 db_service.connect()、create_tables()、disconnect()；移除 document_registry 的 connect/disconnect 调用和 import
- `backend/pyproject.toml` - 添加 `sqlalchemy[asyncio]>=2.0.0`

---

## 7. Bug 修复 / Bug Fix (2026-04-12)

### 文档删除失败修复

**问题 / Issue:** `vector_store.delete_document()` 使用 `filter={"filename": document_id}` 删除文档，但 `document_id` 是 UUID，`filename` 存储的是原始文件名，导致过滤器永远匹配不到任何文档，删除操作静默失败。

**修复 / Fix:**
- `store_document()`: 在创建文档前生成 `doc_id = str(uuid.uuid4())`，将 `doc_id` 写入每个 chunk 的 metadata，返回 `doc_id` 而非 PGVector 的 `ids[0]`
- `delete_document()`: 过滤条件改为 `filter={"doc_id": document_id}`

**修改文件 / Modified Files:**
- `backend/src/services/vector_store.py` (添加 `import uuid`；修改 `store_document` 和 `delete_document`)

---

## 8. 后续改进 / Future Improvements (Day 3+)

- [ ] OCR 支持用于图片 PDF
- [ ] 表格提取
- [ ] 父子分块索引
- [ ] 文档版本控制
