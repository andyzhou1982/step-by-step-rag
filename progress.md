# Progress Log
<!--
  WHAT: RAG 项目的进度日志
  WHY: 记录每个阶段的详细进展
  WHEN: 每个阶段完成或有重要进展时更新
-->

## Session: 2026-03-27~30 (Bug 修复)

### Bug 修复阶段
- **Status:** complete
- **Started:** 2026-03-27
- Actions taken:
  - 修复 BM25 索引构建使用空查询卡住的问题
  - 修复 BM25 索引构建时的事件循环冲突问题
  - 修复 PGVector 表列名错误 (langchain_id, langchain_metadata)
  - 修复文件扩展名解析错误
  - 文档列表持久化到 PostgreSQL（day1-day7 全部修复）
  - 前端支持多种文件格式上传
  - BM25 添加 jieba 中文分词支持
  - 修复 day4-day7 VSCode 导入警告（添加 .vscode/settings.json）
  - 修复流式输出引用提取错误（findall → finditer）
  - 增强全项目错误日志记录（day1-day7 统一添加 logging 模块和完整堆栈输出）
- Files created/modified:
  - day1-day7/backend/src/services/document_registry.py (新增)
  - day1-day7/backend/src/routers/documents.py (修改)
  - day1-day7/backend/src/main.py (修改)
  - day3-day7/backend/src/services/vector_store.py (修改)
  - day3-day7/backend/src/services/retrieval_service.py (添加 jieba)
  - day3-day7/backend/pyproject.toml (添加 jieba 依赖)
  - day3/CHANGES.md (更新文档)
  - task_plan.md (更新错误记录)
  - findings.md (更新问题记录)
  - progress.md (更新进度)
  - day4-day7/backend/src/services/citation_service.py (修复 findall→finditer)

---

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

### Phase 6: Day 5 评估与监控
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：EvaluationService 实现 RAGAS 评估（Faithfulness, Answer Relevance, Context Precision/Recall）
  - 后端：RetrievalMetricsService 实现检索指标（Recall@K, Precision@K, MRR, NDCG）
  - 后端：TracingService 实现 OpenTelemetry 请求追踪
  - 后端：结构化日志（structlog 集成）
  - 后端：新增 /evaluation/* 评估 API 端点
  - 后端：schemas 添加 EvaluationMetrics, RetrievalMetrics, EvaluationRequest 等类型
  - 前端：EvaluationPanel 组件展示评估指标
  - 前端：API 客户端添加评估 API 函数
  - 前端：新增评估标签页
  - 文档：CHANGES.md 核心修改说明
  - 代码编译验证通过
- Files created/modified:
  - day5/backend/src/services/evaluation_service.py (RAGAS 评估)
  - day5/backend/src/services/metrics_service.py (检索指标)
  - day5/backend/src/services/tracing_service.py (请求追踪)
  - day5/backend/src/routers/evaluation.py (评估 API)
  - day5/backend/src/models/schemas.py (Day 5 评估类型)
  - day5/backend/src/config.py (评估配置参数)
  - day5/backend/src/main.py (Day 5 版本)
  - day5/backend/pyproject.toml (ragas, datasets, opentelemetry, structlog)
  - day5/frontend/src/api/client.ts (评估 API 类型)
  - day5/frontend/src/components/EvaluationPanel.tsx (评估面板)
  - day5/frontend/src/App.tsx (Day 5 标题 + 评估标签页)
  - day5/frontend/package.json (版本 5.0.0)
  - day5/CHANGES.md

### Phase 7: Day 6 安全与治理
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：AuthService 实现 JWT 用户认证（注册、登录、token 管理）
  - 后端：PermissionService 实现文档级 ACL 权限控制
  - 后端：AuditService 实现审计日志记录
  - 后端：ContentFilterService 实现内容过滤（SQL 注入、XSS、提示注入）
  - 后端：新增 /auth/* 认证 API 端点
  - 后端：新增 /permissions/* 权限 API 端点
  - 后端：新增 /audit/* 审计 API 端点
  - 后端：schemas 添加 User, Permission, AuditLog 等类型
  - 后端：config.py 添加安全配置参数
  - 前端：LoginPanel 组件实现登录/注册界面
  - 前端：AuditPanel 组件实现审计日志展示
  - 前端：API 客户端添加认证、权限、审计 API 函数
  - 前端：App.tsx 集成认证流程和审计标签页
  - 文档：CHANGES.md 核心修改说明
  - 代码编译验证通过
- Files created/modified:
  - day6/backend/src/services/auth_service.py (JWT 认证)
  - day6/backend/src/services/permission_service.py (ACL 权限)
  - day6/backend/src/services/audit_service.py (审计日志)
  - day6/backend/src/services/content_filter_service.py (内容过滤)
  - day6/backend/src/routers/auth.py (认证 API)
  - day6/backend/src/routers/permissions.py (权限 API)
  - day6/backend/src/routers/audit.py (审计 API)
  - day6/backend/src/models/schemas.py (Day 6 安全类型)
  - day6/backend/src/config.py (安全配置参数)
  - day6/backend/src/main.py (Day 6 版本)
  - day6/backend/pyproject.toml (PyJWT, passlib, python-jose, email-validator)
  - day6/frontend/src/api/client.ts (认证、权限、审计 API 类型)
  - day6/frontend/src/components/LoginPanel.tsx (登录面板)
  - day6/frontend/src/components/AuditPanel.tsx (审计面板)
  - day6/frontend/src/App.tsx (Day 6 标题 + 认证流程)
  - day6/frontend/package.json (版本 6.0.0)
  - day6/CHANGES.md

### Phase 8: Day 7 生产优化
- **Status:** complete
- **Started:** 2026-03-22
- Actions taken:
  - 后端：CacheService 实现内存缓存（TTLCache）和可选 Redis 支持
  - 后端：RetryService 实现指数退避重试逻辑
  - 后端：PerformanceMetrics 实现性能指标收集
  - 后端：更新 config.py 添加生产配置参数
  - 后端：更新 main.py 添加指标端点 /metrics 和 /cache/stats
  - 后端：添加请求计时中间件
  - 后端：创建 Dockerfile（多阶段构建）
  - 前端：更新 package.json 版本到 7.0.0
  - 前端：更新 App.tsx 显示 Day 7 信息和系统状态
  - 前端：创建 Dockerfile（多阶段构建 + nginx）
  - 前端：创建 nginx.conf 配置文件
  - 配置：创建 docker-compose.yml 完整编排配置
  - 文档：创建 readme.md 和 readme_cn.md
  - 文档：创建 CHANGES.md 核心修改说明
  - 代码编译验证通过
- Files created/modified:
  - day7/backend/src/services/cache_service.py (缓存服务)
  - day7/backend/src/services/retry_service.py (重试服务)
  - day7/backend/src/services/performance_service.py (性能指标服务)
  - day7/backend/src/config.py (生产配置参数)
  - day7/backend/src/main.py (Day 7 版本)
  - day7/backend/pyproject.toml (cachetools, redis, tenacity, prometheus-client)
  - day7/backend/Dockerfile (后端 Docker 镜像)
  - day7/frontend/src/App.tsx (Day 7 标题 + 系统状态)
  - day7/frontend/package.json (版本 7.0.0)
  - day7/frontend/Dockerfile (前端 Docker 镜像)
  - day7/frontend/nginx.conf (nginx 配置)
  - day7/docker-compose.yml (完整编排配置)
  - day7/readme.md (英文文档)
  - day7/readme_cn.md (中文文档)
  - day7/CHANGES.md

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
| Day 5 | 评估与监控 | complete | RAGAS + 链路追踪 |
| Day 6 | 安全与治理 | complete | JWT 认证 + ACL 权限 + 审计日志 |
| Day 7 | 生产优化 | complete | 缓存 + 重试 + 指标 + Docker 部署 |

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
| Where am I? | Phase 8: Day 7 生产优化完成 - 项目完成！ |
| Where am I going? | 项目已完成，可以交付使用 |
| What's the goal? | 创建分阶段 RAG 教程项目，从核心功能到完整系统 - 已达成 |
| What have I learned? | 见 findings.md |
| What have I done? | Day 1-7 全部完成，实现了完整的企业级 RAG 系统 |

## Next Actions
<!--
  下一步行动项
-->
1. 项目已完成！可选后续改进：
   - Kubernetes 部署配置
   - 水平自动扩展
   - 日志聚合（ELK/Loki）
   - 分布式追踪（Jaeger）
   - APM 集成（Prometheus/Grafana）
   - 蓝绿部署
   - CI/CD 管道配置

---
*Update after completing each phase or encountering errors*
