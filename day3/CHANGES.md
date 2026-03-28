# Day 3 核心修改文档 / Day 3 Core Changes Documentation

本文档列出了 Day 3 相对于 Day 2 的核心修改及其原因。
This document lists the core changes from Day 2 to Day 3 and the reasons behind them.

---

## 0. Bug 修复 (2026-03-27~28) / Bug Fixes

### BM25 索引构建问题修复

**问题描述 / Issue:**
- BM25 索引构建使用空查询 `asimilarity_search("", k=1000)` 会卡住
- 使用 PGEngine 连接池导致 "Task got Future attached to a different loop" 错误
- PGVector 表列名错误：使用了 `id`, `metadata` 而非实际的 `langchain_id`, `langchain_metadata`

**修复方案 / Solution:**

```python
# vector_store.py 修复

# 1. 添加独立的异步引擎用于直接 SQL 查询
from sqlalchemy.ext.asyncio import create_async_engine

class VectorStoreService:
    def __init__(self):
        # ...
        self._async_engine = None  # 用于 BM25 索引构建

    async def connect(self):
        # ...
        self._async_engine = create_async_engine(self._connection_string)

    async def get_all_documents_for_bm25(self) -> List[Dict]:
        if not self._async_engine:
            return []

        try:
            async with self._async_engine.connect() as conn:
                result = await conn.execute(
                    text(f"SELECT langchain_id, content, langchain_metadata FROM {self._table_name}")
                )
                rows = result.fetchall()
                documents = []
                for row in rows:
                    metadata = row.langchain_metadata
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    documents.append({
                        "chunk_id": str(row.langchain_id) or "",
                        "document_id": metadata.get("source", ""),
                        "content": row.content or "",
                        "filename": metadata.get("filename", "unknown"),
                        "file_type": metadata.get("file_type", "text"),
                    })
                return documents
        except Exception as e:
            print(f"Warning: Failed to get documents for BM25: {e}")
            return []
```

---

### 文档列表持久化修复

**问题描述 / Issue:**
- 文档列表使用内存字典 `document_registry: dict = {}` 存储
- 重启服务后文档列表丢失

**修复方案 / Solution:**

新增 `services/document_registry.py` 服务：

```python
class DocumentRegistryService:
    """文档元数据持久化服务"""

    async def connect(self):
        # 创建 document_registry 表
        async with self._async_engine.connect() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS document_registry (
                    id VARCHAR(255) PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    file_type VARCHAR(100),
                    file_size BIGINT,
                    title VARCHAR(500)
                )
            """))

    async def add_document(doc_id, filename, chunk_count, ...) -> bool
    async def list_documents() -> List[Dict]
    async def delete_document(doc_id) -> bool
```

修改 `routers/documents.py`：
```python
# 旧代码 (内存)
document_registry: dict = {}
document_registry[document_id] = {...}

# 新代码 (数据库)
from services.document_registry import document_registry
await document_registry.add_document(doc_id=document_id, ...)
docs = await document_registry.list_documents()
```

---

## 1. 新增文件 / New Files

### `backend/src/services/retrieval_service.py`

**功能 / Purpose:**
混合检索服务，包含 BM25 索引、查询重写和重排序功能。

**为什么新增 / Why Added:**
- Day 2 仅支持向量检索
- Day 3 需要支持混合检索（向量 + BM25）
- 提升检索准确率

**核心类 / Core Classes:**
```python
class BM25Index:
    """BM25 索引用于关键词搜索 / BM25 index for keyword search"""
    def add_documents(documents: List[Dict])
    def search(query: str, top_k: int) -> List[Tuple[int, float]]

class QueryRewriter:
    """LLM 查询重写服务 / LLM query rewriting service"""
    async def rewrite_query(query: str) -> str
    async def expand_query(query: str) -> List[str]

class ReRanker:
    """结果重排序服务 / Result re-ranking service"""
    async def rerank(query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]

class HybridRetrievalService:
    """混合检索服务 / Hybrid retrieval service"""
    def build_bm25_index(documents: List[Dict])
    async def search(query, vector_search_func, top_k, use_rewrite, use_rerank) -> List[SearchResult]
```

**检索策略 / Retrieval Strategies:**
| 功能 | 实现 | 权重 |
|------|------|------|
| 向量检索 | PGVector 语义搜索 | 0.6 (默认) |
| BM25 检索 | rank-bm25 关键词搜索 | 0.4 (默认) |
| 查询重写 | LLM 改写/扩展 | 可选 |
| 重排序 | Embedding 相似度 | 可选 |

---

## 2. 修改的文件 / Modified Files

### `backend/pyproject.toml`

**修改内容 / Changes:**
```diff
+ # Day 3: Retrieval optimization
+ "rank-bm25>=0.2.2",
+ "numpy>=1.26.0",
```

**原因 / Reason:**
- 添加 BM25 关键词搜索支持 (rank-bm25)
- 添加数值计算库 (numpy)

---

### `backend/src/models/schemas.py`

**修改内容 / Changes:**

#### 新增模型 / New Models:

```python
class RetrievalConfig(BaseModel):
    """检索配置 / Retrieval configuration"""
    use_hybrid: bool = True
    use_rewrite: bool = False
    use_rerank: bool = True
    top_k: int = 5
    vector_weight: float = 0.6
    bm25_weight: float = 0.4

class RetrievalConfigResponse(BaseModel):
    """检索配置响应 / Retrieval config response"""
    config: RetrievalConfig
    available_strategies: List[str]
    features: List[str]
```

#### 修改的模型 / Modified Models:

```python
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    file_types: Optional[List[str]] = None
+   retrieval_config: Optional[RetrievalConfig] = None  # Day 3 新增

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    conversation_id: str
+   retrieval_method: str = "hybrid"      # Day 3 新增
+   query_rewritten: bool = False         # Day 3 新增
+   original_query: Optional[str] = None  # Day 3 新增

class SourceReference(BaseModel):
    # ... existing fields ...
+   file_type: str = "text"  # Day 2 已有，Day 3 继续使用

class HealthResponse(BaseModel):
    # ... existing fields ...
+   day: int = 3              # Day 3 更新
+   bm25_indexed: bool = False  # Day 3 新增
```

**原因 / Reason:**
- 支持自定义检索配置
- 返回检索方法和查询重写信息

---

### `backend/src/config.py`

**修改内容 / Changes:**

```python
class Settings(BaseSettings):
    # ... existing settings ...

+   # Day 3: Retrieval settings
+   # Day 3： 检索设置
+   use_hybrid_search: bool = True
+   use_query_rewrite: bool = False
+   use_rerank: bool = True
+   top_k: int = 5
+   vector_weight: float = 0.6
+   bm25_weight: float = 0.4
```

**原因 / Reason:**
- 提供检索参数的默认配置
- 允许通过环境变量调整检索行为

---

### `backend/src/services/vector_store.py`

**修改内容 / Changes:**

```python
+ async def get_all_documents_for_bm25(self) -> List[Dict]:
+     """
+     Get all documents for BM25 indexing
+     获取所有文档用于 BM25 索引
+
+     Day 3: Added to support BM25 index building
+     Day 3： 添加以支持 BM25 索引构建
+     """
+     try:
+         results = await self.vectorstore.asimilarity_search("", k=1000)
+         documents = []
+         for doc in results:
+             documents.append({
+                 "chunk_id": doc.id or "",
+                 "document_id": doc.metadata.get("source", ""),
+                 "content": doc.page_content,
+                 "filename": doc.metadata.get("filename", "unknown"),
+                 "file_type": doc.metadata.get("file_type", "text"),
+             })
+         return documents
+     except Exception:
+         return []
```

**原因 / Reason:**
- 为 BM25 索引构建提供所有文档
- 使用空查询获取大量结果

---

### `backend/src/routers/documents.py`

**修改内容 / Changes:**

```python
+ from services.retrieval_service import retrieval_service

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # ... existing upload logic ...

+   # Day 3: Rebuild BM25 index with new document
+   # Day 3： 使用新文档重建 BM25 索引
+   try:
+       all_docs = await vector_store.get_all_documents_for_bm25()
+       if all_docs:
+           retrieval_service.build_bm25_index(all_docs)
+   except Exception:
+       pass  # Non-critical error, continue

@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(document_id: str):
    # ... existing delete logic ...

+   # Day 3: Rebuild BM25 index after deletion
+   # Day 3： 删除后重建 BM25 索引
+   try:
+       all_docs = await vector_store.get_all_documents_for_bm25()
+       if all_docs:
+           retrieval_service.build_bm25_index(all_docs)
+   except Exception:
+       pass  # Non-critical error, continue
```

**原因 / Reason:**
- 文档变更时自动更新 BM25 索引
- 失败时不阻塞主流程

---

### `backend/src/routers/chat.py`

**修改内容 / Changes:**

```python
+ from services.retrieval_service import retrieval_service

+ @router.get("/retrieval-config", response_model=RetrievalConfigResponse)
+ async def get_retrieval_config():
+     """获取检索配置 / Get retrieval configuration"""
+     config = RetrievalConfig(
+         use_hybrid=settings.use_hybrid_search,
+         use_rewrite=settings.use_query_rewrite,
+         use_rerank=settings.use_rerank,
+         top_k=settings.top_k,
+         vector_weight=settings.vector_weight,
+         bm25_weight=settings.bm25_weight,
+     )
+     return RetrievalConfigResponse(
+         config=config,
+         available_strategies=["vector", "bm25", "hybrid"],
+         features=["query_rewrite", "rerank"]
+     )

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
+   # Day 3: Get retrieval config from request or use defaults
+   config = request.retrieval_config or RetrievalConfig(...)

+   # Day 3: Use hybrid search if enabled
+   if config.use_hybrid:
+       search_results = await retrieval_service.search(
+           query=request.question,
+           vector_search_func=lambda q, k: vector_store.search_similar(...),
+           top_k=config.top_k,
+           use_rewrite=config.use_rewrite,
+           use_rerank=config.use_rerank,
+       )
+   else:
+       # Vector search only
+       search_results = await vector_store.search_similar(...)

    return ChatResponse(
        answer=answer,
        sources=sources,
        conversation_id=conversation_id,
+       retrieval_method="hybrid" if config.use_hybrid else "vector",
+       query_rewritten=config.use_rewrite,
+       original_query=request.question if config.use_rewrite else None,
    )
```

**原因 / Reason:**
- 支持混合检索和配置
- 返回检索方法信息供前端展示

---

### `backend/src/main.py`

**修改内容 / Changes:**

```python
+ from services.retrieval_service import retrieval_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await vector_store.connect()

+   # Day 3: Build BM25 index from existing documents
+   # Day 3： 从现有文档构建 BM25 索引
+   print("Building BM25 index...")
+   try:
+       documents = await vector_store.get_all_documents_for_bm25()
+       if documents:
+           retrieval_service.build_bm25_index(documents)
+   except Exception as e:
+       print(f"Warning: Failed to build BM25 index: {e}")

    yield
    # Shutdown
    await vector_store.disconnect()

app = FastAPI(
    title="Step-by-Step RAG API",
-   version="2.0.0",
+   version="3.0.0",
    description="""
-   ## Day 2: Enhanced Document Processing
+   ## Day 3: Hybrid Retrieval & Re-ranking

+   ### Day 3 Features:
+   - **Hybrid search**: Vector + BM25 keyword search
+   - **Query rewriting**: Optional LLM-based query optimization
+   - **Re-ranking**: Cross-encoder result re-ranking
    """,
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        database=db_status,
-       version="2.0.0",
-       day=2,
+       version="3.0.0",
+       day=3,
+       bm25_indexed=retrieval_service._bm25_index._index is not None,
    )
```

**原因 / Reason:**
- 启动时自动构建 BM25 索引
- 更新版本号和描述
- 健康检查包含 BM25 索引状态

---

## 3. 前端变更 / Frontend Changes

### `frontend/src/api/client.ts`

**修改内容 / Changes:**

```typescript
+ // Day 3: Retrieval configuration types
+ export interface RetrievalConfig {
+   use_hybrid?: boolean
+   use_rewrite?: boolean
+   use_rerank?: boolean
+   top_k?: number
+   vector_weight?: number
+   bm25_weight?: number
+ }

+ export interface RetrievalConfigResponse {
+   config: RetrievalConfig
+   available_strategies: string[]
+   features: string[]
+ }

export interface ChatRequest {
  question: string
  conversation_id?: string
  file_types?: string[]
+ retrieval_config?: RetrievalConfig  // Day 3 新增
}

export interface ChatResponse {
  answer: string
  sources: SourceReference[]
  conversation_id: string
+ retrieval_method?: string     // Day 3 新增
+ query_rewritten?: boolean     // Day 3 新增
+ original_query?: string | null  // Day 3 新增
}

+ export async function getRetrievalConfig(): Promise<RetrievalConfigResponse> {
+   const response = await api.get<RetrievalConfigResponse>('/chat/retrieval-config')
+   return response.data
+ }
```

---

### `frontend/src/components/ChatInterface.tsx`

**修改内容 / Changes:**

#### 新增状态 / New State:
```typescript
const [config, setConfig] = useState<RetrievalConfig>(DEFAULT_CONFIG)
const [showConfig, setShowConfig] = useState(false)
```

#### 新增配置面板 / New Config Panel:
```tsx
{showConfig && (
  <div className="p-4 border-b bg-gray-50">
    <h3>Retrieval Configuration / 检索配置</h3>
    <div className="grid grid-cols-4 gap-4">
      {/* Hybrid Search Toggle */}
      <label>
        <input type="checkbox" checked={config.use_hybrid} />
        Hybrid Search / 混合检索
      </label>

      {/* Query Rewrite Toggle */}
      <label>
        <input type="checkbox" checked={config.use_rewrite} />
        Query Rewrite / 查询重写
      </label>

      {/* Re-rank Toggle */}
      <label>
        <input type="checkbox" checked={config.use_rerank} />
        Re-rank / 重排序
      </label>

      {/* Top K */}
      <input type="number" value={config.top_k} />
    </div>

    {/* Weight sliders */}
    {config.use_hybrid && (
      <div>
        <input type="range" value={config.vector_weight} />
        <input type="range" value={config.bm25_weight} />
      </div>
    )}
  </div>
)}
```

#### 显示检索信息 / Display Retrieval Info:
```tsx
{/* Retrieval method badge */}
{message.retrievalMethod && (
  <span className="badge">
    {message.retrievalMethod === 'hybrid' && '🔀 Hybrid'}
    {message.retrievalMethod === 'vector' && '📊 Vector'}
  </span>
)}

{/* Query rewritten indicator */}
{message.queryRewritten && (
  <div>
    <span className="badge">✍️ Rewritten</span>
    <div>Original: "{message.originalQuery}"</div>
  </div>
)}
```

---

## 4. 依赖变更 / Dependency Changes

### 新增依赖 / Added Dependencies:

| 包 | 版本 | 用途 |
|----|------|------|
| `rank-bm25` | >=0.2.2 | BM25 关键词搜索算法 |
| `numpy` | >=1.26.0 | 数值计算、余弦相似度 |

---

## 5. API 变更 / API Changes

### 新增端点 / New Endpoints:

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/chat/retrieval-config` | 获取当前检索配置 |

### 修改的请求 / Modified Requests:

**ChatRequest:**
```json
{
  "question": "What is RAG?",
  "conversation_id": "xxx",
  "file_types": ["pdf"],
+ "retrieval_config": {
+   "use_hybrid": true,
+   "use_rewrite": false,
+   "use_rerank": true,
+   "top_k": 5,
+   "vector_weight": 0.6,
+   "bm25_weight": 0.4
+ }
}
```

### 修改的响应 / Modified Responses:

**ChatResponse:**
```json
{
  "answer": "...",
  "sources": [...],
  "conversation_id": "xxx",
+ "retrieval_method": "hybrid",
+ "query_rewritten": false,
+ "original_query": null
}
```

**HealthResponse:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "3.0.0",
  "day": 3,
+ "bm25_indexed": true
}
```

---

## 6. 设计决策 / Design Decisions

### 为什么使用混合检索？

1. **向量检索擅长**: 语义理解、同义词匹配
2. **BM25 擅长**: 精确关键词匹配、专业术语
3. **结合两者**: 覆盖更多场景，提升召回率

### 为什么使用 Embedding 相似度重排序而非 Cross-Encoder？

1. **简单性**: 不需要额外的模型下载
2. **性能**: Embedding 已缓存，计算快
3. **Day 7 改进**: 可替换为真正的 Cross-Encoder

### 为什么 BM25 索引重建是非关键操作？

1. **不阻塞主流程**: 上传/删除成功即可返回
2. **降级运行**: 即使索引失败，向量检索仍可用
3. **启动时重建**: 每次启动都会重新构建索引

### 权重配置为什么是 0.6 向量 + 0.4 BM25？

1. **语义优先**: RAG 场景通常需要语义理解
2. **关键词补充**: BM25 提供精确匹配支持
3. **可调整**: 用户可通过配置调整权重

---

## 7. 后续改进 / Future Improvements (Day 4+)

- [ ] 真正的 Cross-Encoder 重排序模型
- [ ] 查询扩展（生成多个查询变体）
- [ ] 检索结果缓存
- [ ] 检索效果评估指标（Recall, MRR）
- [ ] 自适应权重学习
