# Task Plan: Step-by-Step RAG Tutorial Project
<!--
  WHAT: 企业级 RAG 系统循序渐进教程实施方案
  WHY: 将复杂的企业级 RAG 系统拆解为可学习的阶段性模块
  WHEN: 在开始任何工作之前创建，每个阶段完成后更新
-->

## Goal
<!--
  目标：创建一个循序渐进的教程式 RAG 项目，从最小化实现逐步演进到完整的企业级系统
-->
创建一个分阶段的企业级 RAG 系统教程项目，每个阶段（day）独立可运行，展示从核心功能到完整系统的演进过程。

## Current Phase
Phase 8: Day 7 完成 + Bug 修复

### 最近修复 (2026-03-27~30)
- [x] 修复 BM25 索引构建使用空查询卡住的问题
- [x] 修复 BM25 索引构建时的事件循环冲突问题
- [x] 修复 PGVector 表列名错误 (langchain_id, langchain_metadata)
- [x] 修复文件扩展名解析错误
- [x] 文档列表持久化到 PostgreSQL（day1-day7 全部修复）
- [x] 前端支持多种文件格式上传
- [x] BM25 添加 jieba 中文分词支持

## Technology Stack Decisions
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend | Python + FastAPI | 生态丰富，LangChain 支持最好，异步性能优秀 |
| Frontend | React + TypeScript | 类型安全，组件生态丰富，适合企业级开发 |
| Vector DB | pgvector | 基于 PostgreSQL，支持混合检索，运维简单 |
| LLM | OpenAI Compatible | 灵活切换不同模型，兼容性好 |
| Embedding | text-embedding-3-small | OpenAI 兼容，性价比高 |

## Phases Overview
<!--
  七个阶段，从最小化实现到完整系统
  每个阶段独立目录，可独立运行
-->

### Day 1: 最小化 RAG 实现 (Minimal RAG) ✅
- [x] 创建项目基础结构
- [x] 后端：FastAPI 基础框架 + 文档上传 API
- [x] 后端：文本分块 + 向量存储（pgvector）
- [x] 后端：简单问答 API（向量检索 + LLM 调用）
- [x] 前端：文档上传界面
- [x] 前端：问答对话界面
- [x] 测试：测试用例编写
- **Status:** complete
- **Goal:** 跑通核心 RAG 流程：上传 → 分块 → 存储 → 检索 → 生成

### Day 2: 数据预处理增强 (Enhanced Preprocessing) ✅
- [x] 多格式文档解析（PDF, Word, Markdown, HTML）
- [x] 智能分块策略（递归字符分块 + Markdown/HTML 分割器）
- [x] 元数据提取与存储
- [x] 文档管理 API（列表、删除、支持的格式）
- [x] 前端：复用 Day 1 前端
- [x] 文档：CHANGES.md 核心修改说明
- [x] 代码编译验证通过
- **Status:** complete
- **Goal:** 支持多种文档格式，实现智能分块

### Day 3: 检索优化 (Retrieval Optimization) ✅
- [x] 混合检索（向量 + BM25 关键词）
- [x] 查询重写与扩展
- [x] 重排序（Cross-Encoder）
- [x] 检索参数配置 API
- [x] 前端：检索配置与调试界面
- [x] 代码编译验证通过
- **Status:** complete
- **Goal:** 提升检索准确率，实现混合检索

### Day 4: 生成增强 (Generation Enhancement) ✅
- [x] 引用溯源（Citation）
- [x] 流式输出（Streaming）
- [x] 防幻觉机制（仅基于上下文回答）
- [x] 对话历史管理
- [x] 前端：引用跳转、流式显示
- [x] 代码编译验证通过
- **Status:** complete
- **Goal:** 增强答案可信度，支持引用溯源

### Day 5: 评估与监控 (Evaluation & Observability) ✅
- [x] 离线评估框架（RAGAS 集成）
- [x] 检索指标（Recall, Precision, MRR）
- [x] 生成指标（Faithfulness, Relevance）
- [x] 链路追踪（Request Tracing）
- [x] 前端：评估报告展示
- [x] 代码编译验证通过
- **Status:** complete
- **Goal:** 建立评估体系，实现效果可量化

### Day 6: 安全与治理 (Security & Governance) ✅
- [x] 用户认证（JWT）
- [x] 文档级权限控制（ACL）
- [x] 审计日志
- [x] 输入输出过滤
- [x] 前端：登录、权限管理
- [x] 代码编译验证通过
- **Status:** complete
- **Goal:** 企业级安全控制

### Day 7: 生产优化 (Production Ready) ✅
- [x] 性能优化（缓存、连接池）
- [x] 错误处理与重试
- [x] Docker 部署配置
- [x] 完整文档（README 中英文）
- [x] API 文档（Swagger - 自动生成）
- [x] 最终测试：完整流程验证
- **Status:** complete
- **Goal:** 生产级部署就绪

## Key Questions
1. ~~技术栈选择？~~ → 已确认：Python/FastAPI + React/TS + pgvector
2. 每个阶段的验收标准是什么？ → 见各阶段 Goal
3. 如何保证每个阶段独立可运行？ → 独立目录 + 完整依赖
4. 代码注释格式？ → 双语注释（英文+中文）

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 pgvector 而非独立向量库 | 用户选择，运维简单，支持混合检索 |
| OpenAI 兼容接口 | 灵活切换不同模型供应商 |
| 分阶段独立目录 | 便于学习，每阶段完整可运行 |
| 双语代码注释 | 便于中英文用户学习 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| BM25 索引构建卡住 | 使用空查询 `asimilarity_search("", k=1000)` | 改用直接 SQL 查询获取所有文档 |
| 事件循环冲突 "Task got Future attached to a different loop" | 使用 PGEngine 的连接池 | 创建独立的 `create_async_engine` 用于直接 SQL 查询 |
| PGVector 列名错误 "column 'id' does not exist" | 使用 `id`, `metadata` 列名 | 改为 `langchain_id`, `langchain_metadata` |
| 文档列表重启后丢失 | 使用内存字典 `document_registry` | 持久化到 PostgreSQL `document_registry` 表 |
| 文件扩展名解析错误 | 使用 `filename.split('.')[-1]` | 改用 `Path(filename).suffix.lower()` |
| BM25 中文搜索 score 全为 0.0 | 使用空格分词 `_tokenize` | 添加 `jieba` 进行中文分词 |

## Project Structure
```
step-by-step-rag/
├── day1/                          # 最小化 RAG 实现
│   ├── backend/
│   │   ├── src/
│   │   │   ├── main.py            # FastAPI 入口
│   │   │   ├── config.py          # 配置管理
│   │   │   ├── routers/           # API 路由
│   │   │   ├── services/          # 业务逻辑
│   │   │   └── models/            # 数据模型
│   │   └── test/                  # 测试代码
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx
│       │   ├── components/
│       │   └── api/
│       └── package.json
├── day2/                          # 数据预处理增强
│   └── ...
├── day3/                          # 检索优化
│   └── ...
├── day4/                          # 生成增强
│   └── ...
├── day5/                          # 评估与监控
│   └── ...
├── day6/                          # 安全与治理
│   └── ...
├── day7/                          # 生产优化
│   └── ...
├── requirement.md                 # 需求文档
├── task_plan.md                   # 本文件
├── findings.md                    # 研究发现
├── progress.md                    # 进度日志
├── readme.md                      # 英文文档
└── readme_cn.md                   # 中文文档
```

## Notes
- 每个阶段都是完整可运行的独立项目
- 后续阶段在前一阶段基础上增量添加功能
- 所有代码注释使用双语格式：英文在上，中文在下
- 每阶段完成后需要验证端到端功能
