# Day 5 核心修改文档 / Day 5 Core Changes Documentation

本文档列出了 Day 5 相对于 Day 4 的核心修改及其原因。
This document lists the core changes from Day 4 to Day 5 and the reasons behind them.

---

## 1. 新增文件 / New Files

### `backend/src/services/evaluation_service.py`

**功能 / Purpose:**
RAGAS 评估服务，评估 RAG 系统质量。

**为什么新增 / Why Added:**
- Day 4 没有评估功能
- Day 5 需要支持 RAG 质量量化评估
- 提供置信度之外的多维度评估

**核心类 / Core Classes:**
```python
@dataclass
class RAGEvaluationReport:
    """完整评估报告 / Complete evaluation report"""
    question: str
    answer: str
    contexts: List[str]
    faithfulness_score: float = 0.0
    answer_relevance_score: float = 0.0
    context_precision_score: float = 0.0
    context_recall_score: float = 0.0
    overall_score: float = 0.0

class EvaluationService:
    """RAGAS 评估服务 / RAGAS evaluation service"""

    async def evaluate_single(question, answer, contexts, ground_truth) -> RAGEvaluationReport
    async def evaluate_batch(questions, answers, contexts_list, ground_truths) -> List[RAGEvaluationReport]
    def get_metric_explanation(metric_name) -> str
```

**RAGAS 指标说明 / RAGAS Metrics:**
| 指标 | 描述 | 计算方式 |
|------|------|----------|
| Faithfulness | 答案在上下文中的基础程度 | 检查答案中的声明是否都能从上下文中找到支持 |
| Answer Relevance | 答案与问题的相关程度 | 使用 LLM 评估答案是否直接回应问题 |
| Context Precision | 检索上下文的精确度 | 检索到的相关内容占检索内容的比例 |
| Context Recall | 检索上下文的召回率 | 需要 ground_truth，评估信息覆盖度 |

---

### `backend/src/services/metrics_service.py`

**功能 / Purpose:**
检索指标计算服务，评估搜索质量。

**为什么新增 / Why Added:**
- 需要独立评估检索质量
- 支持多种检索评估指标
- 便于对比不同检索策略

**核心类 / Core Classes:**
```python
@dataclass
class RetrievalMetricsResult:
    """检索指标结果 / Retrieval metrics result"""
    query: str
    k: int = 5
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0

class RetrievalMetricsService:
    """检索指标服务 / Retrieval metrics service"""

    def calculate_recall_at_k(retrieved_ids, relevant_ids, k) -> float
    def calculate_precision_at_k(retrieved_ids, relevant_ids, k) -> float
    def calculate_mrr(retrieved_ids, relevant_ids) -> float
    def calculate_ndcg_at_k(retrieved_ids, relevant_ids, k) -> float
    def evaluate_retrieval(query, retrieved_ids, relevant_ids, k) -> RetrievalMetricsResult
```

**检索指标说明 / Retrieval Metrics:**
| 指标 | 描述 | 适用场景 |
|------|------|----------|
| Recall@K | 检索到的相关项目占所有相关项目的比例 | 评估检索覆盖度 |
| Precision@K | 检索到的项目中相关的比例 | 评估检索精确度 |
| MRR | 第一个相关结果的倒数排名 | 评估最佳结果的位置 |
| NDCG@K | 考虑位置的排序质量 | 评估整体排序质量 |

---

### `backend/src/services/tracing_service.py`

**功能 / Purpose:**
请求追踪服务，使用 OpenTelemetry 实现分布式追踪。

**为什么新增 / Why Added:**
- Day 4 没有请求追踪
- 需要可观测性支持调试和性能分析
- 支持生产环境问题定位

**核心类 / Core Classes:**
```python
@dataclass
class SpanInfo:
    """追踪 Span 信息 / Trace span info"""
    span_id: str
    trace_id: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

@dataclass
class TraceInfo:
    """完整追踪信息 / Complete trace info"""
    trace_id: str
    request_id: str
    operation_type: str
    spans: List[SpanInfo] = field(default_factory=list)

class TracingService:
    """请求追踪服务 / Request tracing service"""

    def start_trace(operation_type, request_id, metadata) -> str
    def end_trace(trace_id) -> Optional[TraceInfo]
    def start_span(trace_id, operation_name, attributes) -> str
    def end_span(span_id, status, events) -> Optional[SpanInfo]
    def add_event(span_id, event_name, attributes)
    def traced(operation_name, operation_type)  # Decorator
```

---

### `backend/src/routers/evaluation.py`

**功能 / Purpose:**
评估 API 路由，提供评估端点。

**新增端点 / New Endpoints:**
```python
@router.post("/rag", response_model=EvaluationResponse)
async def evaluate_rag(request: EvaluationRequest)
    """评估 RAG 质量 / Evaluate RAG quality"""

@router.post("/retrieval")
async def evaluate_retrieval(request: RetrievalEvaluationRequest)
    """评估检索质量 / Evaluate retrieval quality"""

@router.post("/batch", response_model=BatchEvaluationResponse)
async def evaluate_batch(request: BatchEvaluationRequest)
    """批量评估 / Batch evaluation"""

@router.get("/metrics/explanations")
async def get_metric_explanations()
    """获取指标说明 / Get metric explanations"""

@router.get("/health")
async def evaluation_health()
    """评估服务健康检查 / Evaluation health check"""
```

---

## 2. 修改的文件 / Modified Files

### `backend/src/config.py`

**修改内容 / Changes:**

```python
class Settings:
    # ... existing settings ...

+   # Evaluation Configuration (Day 5)
+   # 评估配置（Day 5）
+   evaluation_enabled: bool = os.getenv("EVALUATION_ENABLED", "true").lower() == "true"
+   tracing_enabled: bool = os.getenv("TRACING_ENABLED", "true").lower() == "true"
+   metrics_retention_days: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
```

---

### `backend/src/models/schemas.py`

**修改内容 / Changes:**

#### 新增模型 / New Models:

```python
# Day 5: Evaluation Models
# Day 5： 评估模型
class EvaluationMetrics(BaseModel):
    """RAGAS 评估指标 / RAGAS evaluation metrics"""
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    overall_score: float = 0.0

class RetrievalMetrics(BaseModel):
    """检索质量指标 / Retrieval quality metrics"""
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0

class EvaluationRequest(BaseModel):
    """评估请求 / Evaluation request"""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None

class EvaluationResponse(BaseModel):
    """评估响应 / Evaluation response"""
    rag_metrics: EvaluationMetrics
    retrieval_metrics: Optional[RetrievalMetrics] = None
    evaluation_time_ms: float = 0.0
    timestamp: datetime

class BatchEvaluationRequest(BaseModel):
    """批量评估请求 / Batch evaluation request"""
    questions: List[str]
    answers: List[str]
    contexts_list: List[List[str]]
    ground_truths: Optional[List[str]] = None

class BatchEvaluationResponse(BaseModel):
    """批量评估响应 / Batch evaluation response"""
    results: List[EvaluationResponse]
    average_metrics: EvaluationMetrics
    total_evaluations: int
    total_time_ms: float
```

#### 修改的模型 / Modified Models:

```python
class HealthResponse(BaseModel):
    # ... existing fields ...
    version: str = "5.0.0"  # 更新
    day: int = 5  # 更新
+   evaluation_enabled: bool = True  # Day 5: 评估支持
+   tracing_enabled: bool = True  # Day 5: 追踪支持
```

---

### `backend/src/main.py`

**修改内容 / Changes:**

```python
from routers import documents, chat, evaluation
from services.evaluation_service import evaluation_service
from services.tracing_service import tracing_service

app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
-   ## Day 4: Generation Enhancement with Citations & Streaming
+   ## Day 5: Evaluation & Observability
+   ## Day 5: 评估与可观测性

+   ### Day 5 Features / Day 5 功能:
+   - **RAGAS evaluation**: Faithfulness, Answer Relevance, Context Precision/Recall
+   - **Retrieval metrics**: Recall@K, Precision@K, MRR, NDCG
+   - **Request tracing**: OpenTelemetry-based distributed tracing
+   - **Structured logging**: JSON-formatted logs with structlog

    ### API Endpoints / API 端点:
+   - `POST /evaluation/rag` - Evaluate RAG quality
+   - `POST /evaluation/retrieval` - Evaluate retrieval
+   - `POST /evaluation/batch` - Batch evaluation
+   - `GET /evaluation/metrics/explanations` - Metric docs
""",
-   version="4.0.0",
+   version="5.0.0",
)

app.include_router(evaluation.router)

@app.get("/")
async def root():
    return {
-       "message": "Welcome to Step-by-Step RAG API - Day 4",
+       "message": "Welcome to Step-by-Step RAG API - Day 5",
-       "version": "4.0.0",
+       "version": "5.0.0",
-       "day": 4,
+       "day": 5,
+       "features": [
+           "ragas-evaluation",
+           "retrieval-metrics",
+           "request-tracing",
+           "structured-logging",
            ...
        ],
    }
```

---

## 3. 前端变更 / Frontend Changes

### `frontend/src/api/client.ts`

**修改内容 / Changes:**

```typescript
// Day 5: Evaluation types
// Day 5： 评估类型
export interface EvaluationMetrics {
  faithfulness: number
  answer_relevance: number
  context_precision: number
  context_recall: number
  overall_score: number
}

export interface RetrievalMetrics {
  recall_at_k: number
  precision_at_k: number
  mrr: number
  ndcg_at_k: number
}

export interface EvaluationRequest {
  question: string
  answer: string
  contexts: string[]
  ground_truth?: string
}

export interface EvaluationResponse {
  rag_metrics: EvaluationMetrics
  retrieval_metrics?: RetrievalMetrics
  evaluation_time_ms: number
  timestamp: string
}

// Day 5: Evaluation API functions
// Day 5： 评估 API 函数
+ export async function evaluateRag(request: EvaluationRequest): Promise<EvaluationResponse>
+ export async function getMetricExplanations(): Promise<MetricExplanations>
+ export async function batchEvaluate(request: BatchEvaluationRequest): Promise<BatchEvaluationResponse>
+ export async function evaluationHealth()
```

---

### `frontend/src/components/EvaluationPanel.tsx` (NEW)

**功能 / Purpose:**
评估面板组件，展示 RAGAS 指标和检索质量分数。

**核心组件 / Core Components:**
```tsx
const MetricBar: React.FC<{
  label: string
  value: number
  explanation?: string
}> = ({ label, value, explanation }) => {
  // Color-coded progress bar
  // 颜色编码的进度条
  const getColor = (score: number): string => {
    if (score >= 0.7) return 'bg-green-500'
    if (score >= 0.4) return 'bg-yellow-500'
    return 'bg-red-500'
  }
  // ...
}

const EvaluationPanel: React.FC<EvaluationPanelProps> = ({
  question, answer, contexts, autoEvaluate
}) => {
  // Load explanations, handle evaluation, display results
  // 加载说明、处理评估、显示结果
}
```

---

### `frontend/src/App.tsx`

**修改内容 / Changes:**

```tsx
import EvaluationPanel from './components/EvaluationPanel'

type TabType = 'upload' | 'documents' | 'chat' | 'evaluation'

function App() {
  return (
    <div>
      <header>
        <h1>Step-by-Step RAG
          <span>Day 5: Evaluation & Observability</span>
        </h1>
      </header>

      <nav>
        {/* ... existing tabs ... */}
+       <button onClick={() => setActiveTab('evaluation')}>
+         📊 Evaluation / 评估
+       </button>
      </nav>

      <main>
        {/* ... existing content ... */}
+       {activeTab === 'evaluation' && (
+         <div>
+           <EvaluationPanel ... />
+           {/* Feature descriptions */}
+         </div>
+       )}
      </main>
    </div>
  )
}
```

---

## 4. API 变更 / API Changes

### 新增端点 / New Endpoints:

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/evaluation/rag` | RAGAS 评估 |
| POST | `/evaluation/retrieval` | 检索指标评估 |
| POST | `/evaluation/batch` | 批量评估 |
| GET | `/evaluation/metrics/explanations` | 指标说明 |
| GET | `/evaluation/health` | 评估服务健康检查 |

### 评估请求示例 / Evaluation Request Example:

**POST /evaluation/rag:**
```json
{
  "question": "What is RAG?",
  "answer": "RAG is a technique that combines retrieval with generation...",
  "contexts": [
    "RAG stands for Retrieval-Augmented Generation...",
    "RAG systems use vector databases..."
  ],
  "ground_truth": "RAG is a method that retrieves relevant documents..."
}
```

### 评估响应示例 / Evaluation Response Example:

```json
{
  "rag_metrics": {
    "faithfulness": 0.85,
    "answer_relevance": 0.92,
    "context_precision": 0.80,
    "context_recall": 0.75,
    "overall_score": 0.83
  },
  "evaluation_time_ms": 2500.0,
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 5. 设计决策 / Design Decisions

### 为什么使用 RAGAS？

1. **行业标准**: RAGAS 是 RAG 评估的事实标准
2. **多维度**: 覆盖忠实度、相关性、精确度、召回率
3. **自动化**: 无需人工标注即可评估
4. **可扩展**: 支持自定义指标

### 为什么同时支持检索指标和 RAGAS？

1. **互补**: 检索指标评估搜索质量，RAGAS 评估整体质量
2. **独立调试**: 可以单独定位检索问题或生成问题
3. **灵活性**: 用户可以根据需要选择评估维度

### 为什么使用 OpenTelemetry？

1. **标准化**: OpenTelemetry 是追踪的行业标准
2. **可扩展**: 可以导出到各种后端（Jaeger、Zipkin）
3. **语言无关**: 支持跨服务追踪
4. **丰富上下文**: 支持 span 属性和事件

### 追踪为什么使用内存存储？

1. **简单性**: Day 5 重点是评估功能
2. **开发友好**: 无需额外配置
3. **Day 7 改进**: 生产环境可切换到持久化存储

---

## 6. 依赖变更 / Dependency Changes

### `backend/pyproject.toml` 新增依赖:

```toml
# Evaluation & Observability (Day 5)
"ragas>=0.2.0",               # RAG evaluation framework
"datasets>=3.0.0",            # For Ragas dataset handling
"tqdm>=4.66.0",               # Progress bars for evaluation
"opentelemetry-api>=1.20.0",  # Tracing API
"opentelemetry-sdk>=1.20.0",  # Tracing SDK
"structlog>=24.0.0",          # Structured logging
```

---

## 7. 数据库迁移增强 / Database Migration Enhancement (Post-Release Update)

### 概述 / Overview

Day 5 已完成从原始 SQL 到 SQLAlchemy ORM 的迁移，与 Day 6+ 统一数据库存储方式。

### 新增文件 / New Files

- `backend/src/models/database.py` - ORM 模型定义（DocumentRegistry + QAHistory）
  - QAHistory: id=String(36), confidence=Float（保持与原始表结构兼容）
- `backend/src/services/database_service.py` - 统一数据库连接和会话管理

### 修改文件 / Modified Files

- `backend/src/services/document_registry.py` - 原始 SQL → SQLAlchemy ORM
- `backend/src/services/qa_history_service.py` - 原始 SQL → SQLAlchemy ORM
- `backend/src/main.py` - 添加 db_service 初始化；移除 document_registry 和 qa_history_service 的 connect/disconnect 调用及 import
- `backend/pyproject.toml` - 添加 `sqlalchemy[asyncio]>=2.0.0`

---

## 8. 后续改进 / Future Improvements (Day 6+)

- [ ] 评估结果持久化存储
- [ ] 追踪数据导出到 Jaeger/Zipkin
- [ ] 评估报告可视化图表
- [ ] A/B 测试不同检索策略
- [ ] 实时监控仪表板

---

## 8. Bug 修复记录 / Bug Fix Log

### 2026-04-04: ragas 0.4.x 兼容性修复

**问题描述 / Issue:**
评估功能返回 404 或评估分数为 0/nan。

**根本原因 / Root Causes:**
1. `main.py` 中未注册 evaluation 路由器
2. `pyproject.toml` 缺少 ragas, opentelemetry, structlog 依赖
3. `config.py` 中 `load_dotenv()` 路径错误，导致环境变量未加载
4. ragas 0.4.x API 变更：
   - 列名变更：`question` → `user_input`, `answer` → `response`, `contexts` → `retrieved_contexts`, `ground_truth` → `reference`
   - 需要使用 `LangchainLLMWrapper` 和 `LangchainEmbeddingsWrapper` 包装 LLM
   - `answer_relevancy.strictness=3` 会生成 3 个问题（`n=3`），通义千问 API 不支持
   - 返回 `EvaluationResult` 对象而非字典，需使用 `to_pandas()` 提取结果

**修复内容 / Fixes:**

```python
# main.py: 注册 evaluation 路由器
from routers import documents, chat, evaluation
app.include_router(evaluation.router)

# config.py: 多路径查找 .env 文件
env_paths = [
    Path(__file__).parent.parent / ".env",  # backend/.env
    Path(__file__).parent / ".env",          # src/.env
    Path.cwd() / ".env",                     # current directory
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

# evaluation_service.py: 适配 ragas 0.4.x
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# 设置 strictness=1 兼容通义千问 API
answer_relevancy.strictness = 1

# 使用新的列名
data = {
    "user_input": [question],
    "response": [answer],
    "retrieved_contexts": [contexts],
}
if ground_truth:
    data["reference"] = [ground_truth]

# 包装 LLM 和 embeddings
wrapped_llm = LangchainLLMWrapper(llm)
wrapped_embeddings = LangchainEmbeddingsWrapper(embeddings)

# 使用 to_pandas() 提取结果
df = result.to_pandas()
```

**修改文件 / Modified Files:**
- `day5/backend/src/main.py`
- `day5/backend/pyproject.toml`
- `day5/backend/src/config.py`
- `day5/backend/src/services/evaluation_service.py`
- `day5/frontend/src/components/EvaluationPanel.tsx`

---

### 2026-04-04: QA 历史功能与流式回答保存修复

**问题描述 / Issue:**
评估面板中无法看到问答历史记录。

**根本原因 / Root Causes:**
1. `client.ts` 中存在重复的类型定义（第 461-488 行与第 221-243 行重复）
2. `stream_answer` 函数未调用 `_save_qa_history`，导致流式回答不会保存到历史

**新增功能 / New Features:**

QA 历史持久化存储，用于评估素材：

```python
# backend/src/services/qa_history_service.py (NEW)
class QAHistoryService:
    """QA 历史服务，用于持久化问答记录"""

    async def connect()           # 连接数据库，创建表
    async def add_record()        # 添加问答记录
    async def get_record()        # 获取单条记录
    async def list_records()      # 分页列出记录
    async def delete_record()     # 删除记录
    async def export_records()    # 导出记录用于评估
```

```python
# backend/src/routers/qa_history.py (NEW)
@router.get("")                   # 列出历史（分页）
@router.get("/{record_id}")       # 获取单条记录
@router.delete("/{record_id}")    # 删除记录
@router.post("/export")           # 导出为 JSON
@router.get("/stats/summary")     # 统计摘要
```

**修复内容 / Fixes:**

```python
# chat.py: stream_answer 添加历史保存
# Update conversation
_update_conversation(conversation_id, request.question, full_answer, sources)

# Save QA history for evaluation (NEW)
await _save_qa_history(
    question=request.question,
    answer=full_answer,
    context_chunks=context_chunks,
    sources=sources,
    retrieval_method=retrieval_method,
    confidence=confidence,
    conversation_id=conversation_id
)
```

```typescript
// client.ts: 删除重复的类型定义
// 保留第 212-243 行的定义，删除第 458-488 行的重复定义
```

**前端增强 / Frontend Enhancement:**

```tsx
// EvaluationPanel.tsx: 添加从历史选择功能
const HistoryModal: React.FC = ({ isOpen, onClose, onSelect }) => {
  // 从 QA 历史加载记录
  const loadHistory = async () => {
    const response = await getQAHistoryList(page, pageSize)
    setRecords(response.records || [])
  }
  // 展示历史列表供用户选择
}
```

**修改文件 / Modified Files:**
- `day5/backend/src/services/qa_history_service.py` (NEW)
- `day5/backend/src/routers/qa_history.py` (NEW)
- `day5/backend/src/main.py` (注册路由和服务)
- `day5/backend/src/routers/chat.py` (stream_answer 添加保存)
- `day5/frontend/src/api/client.ts` (删除重复类型、添加 API)
- `day5/frontend/src/components/EvaluationPanel.tsx` (添加历史选择)

---

## 7. Bug 修复 / Bug Fix (2026-04-12)

### 文档删除失败修复

**问题 / Issue:** `vector_store.delete_document()` 使用 `filter={"filename": document_id}` 删除文档，但 `document_id` 是 UUID，`filename` 存储的是原始文件名，导致过滤器永远匹配不到任何文档，删除操作静默失败。

**修复 / Fix:**
- `store_document()`: 在创建文档前生成 `doc_id = str(uuid.uuid4())`，将 `doc_id` 写入每个 chunk 的 metadata，返回 `doc_id` 而非 PGVector 的 `ids[0]`
- `delete_document()`: 过滤条件改为 `filter={"doc_id": document_id}`

**修改文件 / Modified Files:**
- `backend/src/services/vector_store.py` (添加 `import uuid`；修改 `store_document` 和 `delete_document`)
