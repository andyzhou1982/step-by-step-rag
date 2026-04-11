# Day 4 核心修改文档 / Day 4 Core Changes Documentation

本文档列出了 Day 4 相对于 Day 3 的核心修改及其原因。
This document lists the core changes from Day 3 to Day 4 and the reasons behind them.

---

## 1. 新增文件 / New Files

### `backend/src/services/citation_service.py`

**功能 / Purpose:**
引用溯源服务，从 LLM 响应中提取引用并计算置信度评分。

**为什么新增 / Why Added:**
- Day 3 没有引用追踪功能
- Day 4 需要支持答案来源的可追溯性
- 提供置信度评分帮助用户评估答案可靠性

**核心类 / Core Classes:**
```python
@dataclass
class Citation:
    """引用参考数据类 / Citation reference data class"""
    citation_id: int        # 引用编号 [1], [2]
    chunk_id: str           # 分块 ID
    document_id: str        # 文档 ID
    filename: str           # 文件名
    content: str            # 引用内容
    relevance_score: float  # 相关性分数

class CitationService:
    """引用服务类 / Citation service class"""
    CITATION_PATTERN = re.compile(r'\[(\d+)\]|\[Source\s*(\d+)\]')

    def extract_citations(answer, sources) -> List[Citation]
    def calculate_confidence(answer, sources, citations) -> float
    def format_answer_with_citations(answer, sources) -> Tuple[str, List[Citation]]
```

**引用匹配策略 / Citation Matching Strategy:**
| 场景 | 处理方式 |
|------|---------|
| 引用 ID 在范围内 | 匹配对应 source |
| 引用 ID 超出范围 | 分配给第一个 source，降低相关性 |
| 无引用标记 | 返回空列表 |

---

## 2. 修改的文件 / Modified Files

### `backend/src/models/schemas.py`

**修改内容 / Changes:**

#### 新增模型 / New Models:

```python
# Day 4: Streaming models
# Day 4： 流式模型
class StreamChunk(BaseModel):
    """SSE 流式响应分块 / SSE streaming response chunk"""
    type: str  # "content", "sources", "done", "error"
    content: Optional[str] = None
    sources: Optional[List[SourceReference]] = None
    conversation_id: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None

# Day 4: Conversation models
# Day 4： 对话模型
class ConversationMessage(BaseModel):
    """对话消息 / Conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    sources: Optional[List[SourceReference]] = None

class ConversationHistory(BaseModel):
    """对话历史 / Conversation history"""
    conversation_id: str
    messages: List[ConversationMessage]
    message_count: int
    created_at: datetime
    last_updated: datetime

class ConversationSummary(BaseModel):
    """对话摘要 / Conversation summary"""
    conversation_id: str
    preview: str  # 最后一条消息的前 100 字符
    message_count: int
    created_at: datetime
    last_updated: datetime
```

#### 修改的模型 / Modified Models:

```python
class SourceReference(BaseModel):
    # ... existing fields ...
+   citation_id: int = 0  # Day 4: 引用 ID

class ChatRequest(BaseModel):
    # ... existing fields ...
+   stream: bool = False  # Day 4: 是否流式传输
+   max_context_tokens: int = 3000  # Day 4: 最大上下文 token

class ChatResponse(BaseModel):
    # ... existing fields ...
+   confidence: float = 0.0  # Day 4: 置信度评分
+   is_context_based: bool = True  # Day 4: 是否基于上下文
+   context_tokens: int = 0  # Day 4: 上下文 token 数

class HealthResponse(BaseModel):
    version: str = "4.0.0"  # 更新
    day: int = 4  # 更新
+   streaming_enabled: bool = True  # Day 4: 流式支持
```

---

### `backend/src/config.py`

**修改内容 / Changes:**

```python
class Settings:
    # ... existing settings ...

+   # Day 4: Generation Configuration
+   # Day 4： 生成配置
+   max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "3000"))
+   streaming_enabled: bool = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
+   max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
+   confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
```

**原因 / Reason:**
- 提供生成参数的默认配置
- 允许通过环境变量调整流式和上下文行为

---

### `backend/src/services/llm.py`

**修改内容 / Changes:**

```python
class LLMService:
    # Day 4: Enhanced anti-hallucination prompt
    # Day 4： 增强的防幻觉提示
    RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions
STRICTLY based on the provided context documents.

CRITICAL RULES:
1. ONLY use information from the provided context documents
2. If the answer cannot be found, say "I cannot find the answer..."
3. DO NOT make up, infer, or hallucinate any information
4. Use citation numbers [1], [2] when referencing specific documents
5. Always respond in the same language as the user's question

关键规则：
1. 只使用提供的上下文文档中的信息
2. 如果答案无法在上下文中找到，请说"我找不到答案"
3. 不要编造、推断或幻觉任何信息
4. 引用特定文档时使用引用编号 [1], [2] 等
5. 始终用与用户问题相同的语言回答"""

    def _get_llm(self, streaming: bool = False) -> ChatOpenAI:
        """支持流式和非流式 LLM 实例 / Support streaming and non-streaming LLM"""

+   async def generate_response_stream(
+       self, question: str, context: List[str], ...
+   ) -> AsyncIterator[str]:
+       """流式生成响应 / Stream response generation"""
+       async for chunk in llm.astream(messages):
+           if chunk.content:
+               yield chunk.content

+   def estimate_tokens(self, text: str) -> int:
+       """估计文本 token 数量 / Estimate text token count"""
+       # English: ~4 chars/token, Chinese: ~2 chars/token

+   def truncate_context(self, context: List[str], max_tokens: int) -> List[str]:
+       """截断上下文以适应 token 限制 / Truncate context to fit token limit"""
```

**原因 / Reason:**
- 支持流式输出改善用户体验
- 增强 Prompt 减少幻觉
- Token 估算用于上下文管理

---

### `backend/src/routers/chat.py`

**修改内容 / Changes:**

#### 新增端点 / New Endpoints:

```python
+ @router.get("/conversations", response_model=List[ConversationSummary])
+ async def list_conversations():
+     """列出所有对话 / List all conversations"""

+ @router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
+ async def get_conversation(conversation_id: str):
+     """获取对话历史 / Get conversation history"""

+ @router.post("/stream")
+ async def stream_answer(request: ChatRequest):
+     """流式回答（SSE）/ Stream answer (SSE)"""
+     async def generate():
+         # Send sources first
+         yield f"data: {sources_chunk.model_dump_json()}\n\n"
+
+         # Stream content
+         async for text_chunk in llm_service.generate_response_stream(...):
+             yield f"data: {content_chunk.model_dump_json()}\n\n"
+
+         # Send done with confidence
+         yield f"data: {done_chunk.model_dump_json()}\n\n"
+
+     return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 修改的端点 / Modified Endpoints:

```python
@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
+   # Day 4: Add citation_id to sources
+   sources.append(SourceReference(
+       ...,
+       citation_id=i + 1,
+   ))

+   # Day 4: Truncate context if needed
+   context_chunks = llm_service.truncate_context(
+       context_chunks, max_tokens=request.max_context_tokens
+   )

+   # Day 4: Calculate confidence score
+   citations = citation_service.extract_citations(answer, search_results)
+   confidence = citation_service.calculate_confidence(answer, search_results, citations)

+   # Day 4: Check if answer is context-based
+   is_context_based = _is_context_based(answer)

    return ChatResponse(
        ...,
+       confidence=confidence,
+       is_context_based=is_context_based,
+       context_tokens=context_tokens,
    )
```

#### 新增辅助函数 / New Helper Functions:

```python
+ def _get_conversation_history(conversation_id: str) -> List[Dict]:
+     """获取对话历史，限制长度 / Get conversation history with length limit"""

+ def _update_conversation(conversation_id, question, answer, sources):
+     """更新对话，包含元数据 / Update conversation with metadata"""

+ def _is_context_based(answer: str) -> bool:
+     """检查答案是否基于上下文 / Check if answer is based on context"""
```

---

### `backend/src/main.py`

**修改内容 / Changes:**

```python
app = FastAPI(
    title="Step-by-Step RAG API",
    description="""
-   ## Day 3: Hybrid Retrieval & Re-ranking
+   ## Day 4: Generation Enhancement with Citations & Streaming

+   ### Day 4 Features / Day 4 功能:
+   - **Streaming responses**: Real-time answer generation via SSE
+   - **Citation tracking**: Track which sources contribute to the answer
+   - **Confidence scoring**: Evaluate answer reliability
+   - **Anti-hallucination**: Strict context-based response generation

    ### API Endpoints / API 端点:
+   - `POST /chat/stream` - Ask question (streaming SSE)
+   - `GET /chat/conversations` - List conversations
+   - `GET /chat/conversations/{id}` - Get conversation history
""",
-   version="3.0.0",
+   version="4.0.0",
)

@app.get("/")
async def root():
    return {
-       "message": "Welcome to Step-by-Step RAG API - Day 3",
+       "message": "Welcome to Step-by-Step RAG API - Day 4",
-       "version": "3.0.0",
+       "version": "4.0.0",
-       "day": 3,
+       "day": 4,
+       "features": [
+           "streaming",
+           "citations",
+           "confidence-scoring",
+           "anti-hallucination",
            ...
        ],
    }

@app.get("/health")
async def health_check():
    return HealthResponse(
-       version="3.0.0",
-       day=3,
+       version="4.0.0",
+       day=4,
+       streaming_enabled=settings.streaming_enabled,
    )
```

---

## 3. 前端变更 / Frontend Changes

### `frontend/src/api/client.ts`

**修改内容 / Changes:**

```typescript
// Day 4: New types
// Day 4： 新类型
export interface StreamChunk {
  type: 'content' | 'sources' | 'done' | 'error'
  content?: string
  sources?: SourceReference[]
  conversation_id?: string
  confidence?: number
  error?: string
}

export interface ConversationMessage { ... }
export interface ConversationHistory { ... }
export interface ConversationSummary { ... }

// Modified types
export interface SourceReference {
  // ... existing fields ...
+ citation_id?: number  // Day 4
}

export interface ChatRequest {
  // ... existing fields ...
+ stream?: boolean  // Day 4
+ max_context_tokens?: number  // Day 4
}

export interface ChatResponse {
  // ... existing fields ...
+ confidence?: number  // Day 4
+ is_context_based?: boolean  // Day 4
+ context_tokens?: number  // Day 4
}

// New functions
+ export async function askQuestionStream(
+   request: ChatRequest,
+   onChunk: (chunk: StreamChunk) => void,
+   onError?: (error: string) => void
+ ): Promise<void> {
+   const response = await fetch(`${API_BASE_URL}/chat/stream`, ...)
+   const reader = response.body?.getReader()
+   // Process SSE stream...
+ }

+ export async function getConversations(): Promise<ConversationSummary[]>
+ export async function getConversation(id: string): Promise<ConversationHistory>
```

---

### `frontend/src/components/ChatInterface.tsx`

**修改内容 / Changes:**

#### 新增状态 / New State:
```typescript
// Day 4: Streaming and citation state
// Day 4： 流式和引用状态
const [useStreaming, setUseStreaming] = useState(true)
const [selectedCitation, setSelectedCitation] = useState<SourceReference | null>(null)
```

#### 新增配置选项 / New Config Options:
```tsx
{/* Day 4: Streaming toggle */}
{/* Day 4： 流式开关 */}
<label className="flex items-center space-x-2">
  <input type="checkbox" checked={useStreaming}
         onChange={(e) => setUseStreaming(e.target.checked)} />
  <span>Stream / 流式</span>
</label>
```

#### 流式处理函数 / Streaming Handler:
```typescript
const handleSendStreaming = async (userMessage: Message) => {
  // Create placeholder message
  const streamingMessage: Message = {
    id: streamingMessageId,
    role: 'assistant',
    content: '',
    isStreaming: true,
  }
  setMessages(prev => [...prev, streamingMessage])

  await askQuestionStream(
    { question, conversation_id, retrieval_config, stream: true },
    (chunk: StreamChunk) => {
      if (chunk.type === 'content') {
        // Append content with streaming animation
        fullContent += chunk.content
        updateMessage(streamingMessageId, { content: fullContent })
      } else if (chunk.type === 'sources') {
        updateMessage(streamingMessageId, { sources: chunk.sources })
      } else if (chunk.type === 'done') {
        updateMessage(streamingMessageId, {
          confidence: chunk.confidence,
          isStreaming: false
        })
      }
    }
  )
}
```

#### 引用渲染 / Citation Rendering:
```tsx
const renderAnswerWithCitations = (content: string, sources?: SourceReference[]) => {
  const citationRegex = /\[(\d+)\]/g
  // Replace [1], [2] with clickable buttons
  return parts.map(part => {
    if (isCitation) {
      return (
        <button onClick={() => handleCitationClick(source)}
                className="w-5 h-5 bg-blue-500 text-white rounded-full">
          {citationNum}
        </button>
      )
    }
    return part
  })
}
```

#### 引用详情面板 / Citation Detail Panel:
```tsx
{selectedCitation && (
  <div className="w-64 border-l bg-gray-50 p-4">
    <h3>Citation / 引用</h3>
    <p>File: {selectedCitation.filename}</p>
    <p>Score: {(selectedCitation.score * 100).toFixed(1)}%</p>
    <p>Content: {selectedCitation.content}</p>
  </div>
)}
```

#### 置信度显示 / Confidence Display:
```tsx
{message.confidence !== undefined && (
  <span className={getConfidenceBadgeColor(message.confidence)}>
    📊 {(message.confidence * 100).toFixed(0)}%
  </span>
)}
```

---

## 4. API 变更 / API Changes

### 新增端点 / New Endpoints:

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/chat/stream` | 流式问答（SSE）|
| GET | `/chat/conversations` | 列出所有对话 |
| GET | `/chat/conversations/{id}` | 获取对话历史 |

### 修改的请求 / Modified Requests:

**ChatRequest:**
```json
{
  "question": "What is RAG?",
  "conversation_id": "xxx",
  "file_types": ["pdf"],
  "retrieval_config": { ... },
+ "stream": true,
+ "max_context_tokens": 3000
}
```

### 修改的响应 / Modified Responses:

**ChatResponse:**
```json
{
  "answer": "RAG is... [1] [2]",
  "sources": [
    {
      "document_id": "doc1",
      "filename": "doc.pdf",
      "content": "...",
      "score": 0.85,
      "file_type": "pdf",
      "source": "hybrid",
+     "citation_id": 1
    }
  ],
  "conversation_id": "conv-123",
  "retrieval_method": "hybrid",
  "query_rewritten": false,
+ "confidence": 0.75,
+ "is_context_based": true,
+ "context_tokens": 1500
}
```

**SSE StreamChunk (type=content):**
```json
{
  "type": "content",
  "content": "RAG is ",
  "conversation_id": "conv-123"
}
```

**SSE StreamChunk (type=done):**
```json
{
  "type": "done",
  "conversation_id": "conv-123",
  "confidence": 0.75
}
```

---

## 5. 设计决策 / Design Decisions

### 为什么使用 SSE 而非 WebSocket？

1. **简单性**: 单向数据流足够，无需双向通信
2. **兼容性**: HTTP 协议，穿透防火墙更好
3. **重连**: 浏览器自动重连机制
4. **适用场景**: 服务器向客户端推送，正是流式输出的需求

### 为什么置信度使用启发式方法？

1. **性能**: 不需要额外的 LLM 调用
2. **简单性**: 基于可观察特征的简单计算
3. **可解释性**: 用户可以理解评分依据
4. **Day 7 改进**: 可替换为更复杂的评估模型

### 引用 ID 为什么从 1 开始？

1. **用户友好**: [1], [2] 比 [0], [1] 更自然
2. **学术惯例**: 学术论文使用 1-based 编号
3. **前端一致性**: 显示编号与数组索引解耦

### 对话历史为什么限制为 20 条？

1. **性能**: 避免过长的上下文影响响应速度
2. **成本**: 减少 LLM token 消耗
3. **效果**: 过长历史可能引入噪音
4. **可配置**: 通过 MAX_HISTORY_MESSAGES 环境变量调整

---

## 6. 数据库迁移增强 / Database Migration Enhancement (Post-Release Update)

### 概述 / Overview

Day 4 已完成从原始 SQL 到 SQLAlchemy ORM 的迁移，与 Day 6+ 统一数据库存储方式。

### 新增文件 / New Files

- `backend/src/models/database.py` - ORM 模型定义（DocumentRegistry）
- `backend/src/services/database_service.py` - 统一数据库连接和会话管理

### 修改文件 / Modified Files

- `backend/src/services/document_registry.py` - 原始 SQL → SQLAlchemy ORM
- `backend/src/main.py` - 添加 db_service 初始化；移除 document_registry 的 connect/disconnect 调用和 import
- `backend/pyproject.toml` - 添加 `sqlalchemy[asyncio]>=2.0.0`

---

## 7. 后续改进 / Future Improvements (Day 5+)

- [ ] 真正的引用提取（LLM 输出解析）
- [ ] 流式 token 计数和显示
- [ ] 更精细的置信度模型
- [ ] 对话摘要功能
- [ ] 引用高亮（在原文中定位）

