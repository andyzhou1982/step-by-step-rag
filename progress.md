# Progress Log
<!--
  WHAT: RAG 项目的进度日志
  WHY: 记录每个阶段的详细进展
  WHEN: 每个阶段完成或有重要进展时更新
-->

## Session: 2026-03-22

### Phase 1: 技术栈确认与规划
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 读取 requirement.md 需求文档
  - 确认项目目标：创建循序渐进的 RAG 教程项目
  - 确认技术栈选择：
    - 后端：Python + FastAPI
    - 前端：React + TypeScript
    - 向量数据库：pgvector
    - LLM：OpenAI 兼容接口
  - 创建 task_plan.md 分阶段规划
  - 创建 findings.md 技术研究记录
  - 创建 progress.md 进度日志
- Files created/modified:
  - task_plan.md (created)
  - findings.md (created)
  - progress.md (created)

### Phase 2: Day 1 实现
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 创建 day1 目录结构
  - 后端：FastAPI 框架 + 配置管理 + 数据模型
  - 后端：Embedding 服务 + LLM 服务 + 向量存储服务（使用 LangChain）
  - 后端：文档上传/列表/删除 API + 问答 API
  - 前端：React + TypeScript + Tailwind CSS 配置
  - 前端：API 客户端 + 文档上传/列表/聊天组件
  - 测试：pytest 测试用例
  - 文档：README 中英文 + QUICKSTART 快速测试指南
  - 配置：.gitignore + docker-compose.yml
  - 测试数据：sample_knowledge.txt
  - 代码编译验证通过
- Files created/modified:
  - day1/backend/pyproject.toml (uv 依赖管理)
  - day1/backend/.env (环境变量配置)
  - day1/backend/.env.example (环境变量示例)
  - day1/backend/src/config.py (dotenv 加载)
  - day1/backend/src/models/schemas.py
  - day1/backend/src/services/embedding.py (LangChain OpenAIEmbeddings)
  - day1/backend/src/services/llm.py (LangChain ChatOpenAI)
  - day1/backend/src/services/vector_store.py (LangChain PGVector)
  - day1/backend/src/routers/documents.py (LangChain RecursiveCharacterTextSplitter)
  - day1/backend/src/routers/chat.py
  - day1/backend/src/main.py
  - day1/backend/test/test_main.py
  - day1/frontend/package.json
  - day1/frontend/src/App.tsx
  - day1/frontend/src/components/*.tsx
  - day1/frontend/src/api/client.ts
  - day1/readme.md
  - day1/readme_cn.md
  - day1/QUICKSTART.md (快速测试指南)
  - day1/docker-compose.yml (PostgreSQL + pgvector)
  - day1/test_data/sample_knowledge.txt (测试数据)
  - .gitignore

### Phase 3: Day 2 数据预处理增强
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：多格式文档解析器（PDF, Word, Markdown, HTML, TXT）
  - 后端：LangChain 智能分块策略（递归字符 + Markdown/HTML 分割器）
  - 后端：元数据提取与存储
  - 后端：文档管理 API（列表、删除、支持的格式查询）
  - 前端：复用 Day 1 前端
  - 文档：CHANGES.md 核心修改说明
  - 代码编译验证通过
- Files created/modified:
  - day2/backend/src/services/document_parser.py (多格式解析器)
  - day2/backend/src/routers/documents.py (增强版)
  - day2/backend/src/models/schemas.py (新增元数据模型)
  - day2/backend/src/services/vector_store.py (支持元数据存储)
  - day2/backend/src/main.py (Day 2 版本)
  - day2/backend/pyproject.toml (新增依赖)
  - day2/CHANGES.md

### Phase 4: Day 3 检索优化
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：BM25Index 类实现关键词搜索
  - 后端：QueryRewriter 类实现查询重写
  - 后端：ReRanker 类实现结果重排序
  - 后端：HybridRetrievalService 实现混合检索服务
  - 后端：向量存储添加 get_all_documents_for_bm25() 方法
  - 后端：文档上传/删除后自动重建 BM25 索引
  - 后端：检索配置 API 端点
  - 前端：检索配置面板（混合检索、查询重写、重排序开关）
  - 前端：显示检索方法和查询重写信息
  - 代码编译验证通过
- Files created/modified:
  - day3/backend/src/services/retrieval_service.py (BM25 + 查询重写 + 重排序)
  - day3/backend/src/services/vector_store.py (添加 BM25 支持方法)
  - day3/backend/src/routers/documents.py (索引重建)
  - day3/backend/src/routers/chat.py (检索配置支持)
  - day3/backend/src/config.py (检索配置参数)
  - day3/backend/src/models/schemas.py (RetrievalConfig 类型)
  - day3/backend/src/main.py (启动时构建 BM25 索引)
  - day3/backend/pyproject.toml (新增 rank-bm25, numpy 依赖)
  - day3/frontend/src/api/client.ts (检索配置 API 类型)
  - day3/frontend/src/components/ChatInterface.tsx (检索配置面板)
  - day3/frontend/src/App.tsx (Day 3 标题)
  - day3/frontend/package.json (版本 3.0.0)

### Phase 5: Day 4 生成增强
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：CitationService 实现引用提取和置信度评分
  - 后端：LLMService 添加流式输出支持（SSE）
  - 后端：增强防幻觉 Prompt 模板
  - 后端：对话历史管理（限制长度、元数据）
  - 后端：新增 /chat/stream SSE 流式端点
  - 后端：新增 /chat/conversations 对话管理端点
  - 后端：schemas 添加 citation_id、confidence、is_context_based 等字段
  - 前端：流式显示支持（SSE EventSource）
  - 前端：可点击的引用标记 [1], [2] 等
  - 前端：引用详情侧边栏
  - 前端：置信度评分显示
  - 前端：流式/非流式模式切换
  - 代码编译验证通过
- Files created/modified:
  - day4/backend/src/services/citation_service.py (引用提取 + 置信度计算)
  - day4/backend/src/services/llm.py (流式输出 + token 估算)
  - day4/backend/src/routers/chat.py (流式端点 + 对话管理)
  - day4/backend/src/models/schemas.py (Day 4 类型)
  - day4/backend/src/config.py (生成配置参数)
  - day4/backend/src/main.py (Day 4 版本)
  - day4/frontend/src/api/client.ts (流式 API + 新类型)
  - day4/frontend/src/components/ChatInterface.tsx (流式 UI + 引用交互)
  - day4/frontend/src/App.tsx (Day 4 标题)
  - day4/frontend/package.json (版本 4.0.0)

## Daily Progress Plan
<!--
  每日计划与实际进度对比
-->

| Day | Plan | Status | Key Deliverables |
|-----|------|--------|------------------|
| Day 1 | 最小化 RAG | complete | 文档上传 + 问答 |
| Day 2 | 数据预处理增强 | complete | 多格式解析 + 智能分块 |
| Day 3 | 检索优化 | complete | 混合检索 + 重排序 |
| Day 4 | 生成增强 | complete | 引用溯源 + 流式输出 |
| Day 5 | 评估与监控 | pending | RAGAS + 链路追踪 |
| Day 6 | 安全与治理 | pending | 认证 + 权限 + 审计 |
| Day 7 | 生产优化 | pending | Docker + 文档 |

## Test Results
<!--
  测试结果记录
-->
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| (待各阶段完成后记录) | | | | |

## Error Log
<!--
  错误日志
-->
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| (暂无) | | | |

## 5-Question Reboot Check
<!--
  上下文检查：如果能回答这 5 个问题，说明上下文完整
-->
| Question | Answer |
|----------|--------|
| Where am I? | Phase 5: Day 4 生成增强完成 |
| Where am I going? | Phase 6: Day 5 评估与监控 |
| What's the goal? | 创建分阶段 RAG 教程项目，从核心功能到完整系统 |
| What have I learned? | 见 findings.md |
| What have I done? | Day 1-4 完成，实现了最小化 RAG + 多格式解析 + 混合检索 + 引用溯源/流式输出 |

## Next Actions
<!--
  下一步行动项
-->
1. 开始 Day 5 实现：
   - RAGAS 离线评估框架
   - 检索指标（Recall, Precision, MRR）
   - 生成指标（Faithfulness, Relevance）
   - 链路追踪（Request Tracing）
   - 前端：评估报告展示
   - 测试：评估流程验证

---
*Update after completing each phase or encountering errors*
