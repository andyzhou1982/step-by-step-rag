# Findings & Decisions
<!--
  WHAT: RAG 项目的研究发现和技术决策记录
  WHY: 持久化存储关键信息，防止上下文丢失
  WHEN: 每次有新发现时更新
-->

## Requirements Summary
<!--
  从 requirement.md 提取的核心需求
-->
企业级 RAG 系统六大核心模块：
1. **数据接入与预处理** - 多源连接器、多格式解析、智能分块
2. **知识存储与管理** - 向量数据库、元数据存储、索引更新
3. **检索与排序** - 查询理解、混合检索、重排序、权限过滤
4. **生成与增强** - Prompt 工程、LLM 集成、引用溯源、防幻觉
5. **评估与可观测性** - 离线评估、在线监控、链路追踪
6. **安全与治理** - 访问控制、数据隐私、审计日志

## Technical Stack Details
<!--
  技术栈详细说明
-->

### Backend (Python + FastAPI)
| Component | Library | Purpose |
|-----------|---------|---------|
| Web Framework | FastAPI | 高性能异步 API |
| Embedding | sentence-transformers / OpenAI | 文本向量化 |
| LLM Client | openai (compatible) | 调用 LLM |
| PDF Parser | PyPDF2 / pdfplumber | PDF 解析 |
| Word Parser | python-docx | Word 解析 |
| Database | asyncpg + pgvector | 向量存储 |

### Frontend (React + TypeScript)
| Component | Library | Purpose |
|-----------|---------|---------|
| Framework | React 18 | UI 框架 |
| Language | TypeScript | 类型安全 |
| HTTP Client | axios | API 调用 |
| UI Components | Tailwind CSS | 样式 |
| Markdown | react-markdown | 渲染 Markdown |

### Vector Database (pgvector)
| Feature | Description |
|---------|-------------|
| Storage | 向量 + 元数据 + 原始文本 |
| Index | IVFFlat / HNSW |
| Search | 余弦相似度 / 欧氏距离 |
| Hybrid | 支持向量 + 全文检索 |

## Research Findings
<!--
  关键研究发现
-->

### RAG 核心流程
```
1. Ingest: 文档上传 → 解析 → 分块
2. Embed: 分块文本 → Embedding 模型 → 向量
3. Store: 向量 + 元数据 → pgvector
4. Retrieve: 问题 → Embedding → 相似度搜索 → Top-K 分块
5. Generate: 问题 + 检索上下文 → LLM → 答案
```

### 分块策略对比
| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| Fixed Size | 简单 | 可能切断语义 | 简单文本 |
| Recursive | 保持段落完整 | 需要调参 | 通用场景 |
| Semantic | 语义完整 | 计算开销大 | 技术文档 |
| Parent-Child | 检索精准+上下文完整 | 实现复杂 | 企业应用 |

### 检索策略对比
| Strategy | Description | When to Use |
|----------|-------------|-------------|
| Vector Only | 语义相似度 | 通用场景 |
| Keyword Only (BM25) | 精确匹配 | 专业术语 |
| Hybrid | 向量 + 关键词 | 最佳效果 |
| Re-ranking | 二次排序 | 高精度需求 |

## Technical Decisions
<!--
  技术决策记录
-->
| Decision | Rationale |
|----------|-----------|
| pgvector vs 独立向量库 | 用户选择，PostgreSQL 扩展，运维简单，支持混合检索 |
| FastAPI vs Flask | FastAPI 异步性能好，自动生成 API 文档 |
| React vs Vue | React 生态更大，TypeScript 支持更成熟 |
| 分阶段独立目录 | 便于学习，每阶段可独立运行和对比 |
| OpenAI 兼容接口 | 可灵活切换 OpenAI/Claude/国内模型 |
| Day 1 最小化实现 | 先跑通流程，后续逐步增强 |

## Implementation Patterns
<!--
  实现模式参考
-->

### Bilingual Comments Format
```python
# Initialize the FastAPI application
# 初始化 FastAPI 应用
app = FastAPI()

def embed_text(text: str) -> list[float]:
    """
    Convert text to embedding vector
    将文本转换为嵌入向量

    Args:
        text: Input text to embed
              需要嵌入的输入文本
    Returns:
        Embedding vector
        嵌入向量
    """
    pass
```

### API Response Format
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### Error Handling Pattern
```python
try:
    # Process document
    # 处理文档
    result = await process_document(file)
except FileNotFoundError as e:
    # File not found error
    # 文件未找到错误
    raise HTTPException(status_code=404, detail=str(e))
```

## Resources
<!--
  有用的资源和参考
-->
- LangChain Documentation: https://python.langchain.com/docs/
- pgvector Documentation: https://github.com/pgvector/pgvector
- FastAPI Documentation: https://fastapi.tiangolo.com/
- RAGAS Evaluation: https://docs.ragas.io/
- RAG Best Practices: https://blog.langchain.dev/deconstructing-rag/

## Issues Encountered
<!--
  遇到的问题和解决方案
-->
| Issue | Resolution |
|-------|------------|
| (暂无) | - |

## Visual/Browser Findings
<!--
  多模态内容记录
-->
- (暂无)

## Day 3 Research: Hybrid Retrieval Implementation
/*
  Day 3 研究：混合检索实现
  Updated: 2026-03-22
*/
### Key Components
1. **BM25Index Class**
   - Uses rank-bm25 library (BM25Okapi)
   - Simple tokenization: lowercase + split on whitespace/punctuation
   - Returns (index, score) pairs for result merging

2. **QueryRewriter Class**
   - Uses LLM to improve/expand queries
   - REWRITE_PROMPT: Clarifies terms, adds synonyms
   - EXPAND_PROMPT: Generates 3 alternative versions
   - Fallback to original query on failure

3. **ReRanker Class**
   - Uses embedding similarity for re-ranking (not cross-encoder due to complexity)
   - Cosine similarity between query and content embeddings
   - Combined score: 0.3 * original + 0.7 * similarity

4. **HybridRetrievalService**
   - Configurable weights: 0.6 vector + 0.4 BM25 (default)
   - Parallel execution: vector search and BM25 in parallel
   - Score normalization before merging
   - Optional query rewrite and re-rank steps

### Configuration
```python
# Day 3 retrieval settings
# Day 3 检索设置
use_hybrid_search: bool = True
use_query_rewrite: bool = False
use_rerank: bool = True
top_k: int = 5
vector_weight: float = 0.6
bm25_weight: float = 0.4
```

### BM25 Index Management
- Built on startup from existing documents
- Rebuilt on document upload/delete
- Non-critical: failures don't block main operations

### Frontend Integration
- RetrievalConfigPanel with toggles for hybrid/rewrite/rerank
- Display badges showing retrieval method (hybrid/vector/bm25)
- Show query rewrite indicator with original query

## Day 4 Research: Citation & Streaming Implementation
/*
  Day 4 研究：引用溯源与流式输出实现
  Updated: 2026-03-22
*/
### Key Components

1. **CitationService Class**
   - Extracts citations from answer text using regex
   - Matches citation IDs [1], [2] to source documents
   - Calculates confidence score based on citation coverage
   - Confidence formula: base (0.8 max) + citation_boost (0.3 max) - penalty

2. **LLMService Streaming Support**
   - generate_response_stream(): AsyncIterator[str] for SSE
   - Uses LangChain's astream() method
   - Token estimation: ~4 chars/token (English), ~2 chars/token (Chinese)
   - Context truncation to fit within token limits

3. **Enhanced Anti-Hallucination Prompt**
   - Strict rules: ONLY use provided context
   - Citation instructions: Use [1], [2] format
   - Fallback: Say "cannot find" if info not in context

4. **Streaming Chat Endpoint (/chat/stream)**
   - SSE (Server-Sent Events) response format
   - StreamChunk types: content, sources, done, error
   - Headers: no-cache, keep-alive, X-Accel-Buffering: no

5. **Conversation Management**
   - In-memory storage with metadata (created_at, updated_at)
   - Message limit: MAX_HISTORY_MESSAGES = 20
   - New endpoints: GET /conversations, GET /conversations/{id}

### Configuration
```python
# Day 4 generation settings
# Day 4 生成设置
max_context_tokens: int = 3000
streaming_enabled: bool = True
max_history_messages: int = 20
confidence_threshold: float = 0.5
```

### Frontend Integration
- Stream toggle: Enable/disable SSE streaming
- Citation parsing: Replace [1], [2] with clickable buttons
- Citation panel: Show selected citation details
- Confidence badge: Color-coded (green >70%, yellow 40-70%, red <40%)
- Streaming indicator: Blinking cursor animation

### Confidence Score Algorithm
```
confidence = min(1.0, base_confidence + citation_boost - lower_confidence)
where:
  base_confidence = min(len(sources) / 5, 0.8)
  citation_boost = min(citations_used / total_sources, 1.0) * 0.3
  lower_confidence = 0.3 if "cannot find" in answer else 0.0
```

---
*Update this file after every 2 view/browser/search operations*
