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
Phase 2: 三种 RAG 架构融合 (Day 8-13)

### 总体目标
在已完成的传统 RAG (Day 1-7) 基础上，新增 LLM Wiki（知识编译型）和 GraphRAG（图增强型）两种 RAG 架构，最终通过智能路由统一入口，由 LLM 自动判断使用哪种 RAG 模型进行问答。

### 架构概览
```
用户提问
  ↓
智能路由 (LLM 判断)
  ↓ (并行/串行)
  ├── 传统 RAG (Day 1-7) → 向量检索 + LLM 生成
  ├── LLM Wiki (Day 8-9) → Wiki 页面语义匹配
  └── GraphRAG (Day 10-11) → 图遍历 + 多跳推理
  ↓
结果融合 → 最终答案
```

### 三种架构定位
| 架构 | 核心能力 | 适合场景 |
|------|----------|----------|
| 传统 RAG | 高保真原文检索、精确事实查找 | FAQ、细节查询、动态数据 |
| LLM Wiki | 高层语义理解、概念综合、长期知识积累 | 研究综述、概念解释、跨文档总结 |
| GraphRAG | 实体关系推理、多跳逻辑、结构化知识 | 关系查询、因果推理、知识网络探索 |

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
  十三个阶段：传统 RAG (Day 1-7) + LLM Wiki (Day 8-9) + GraphRAG (Day 10-11) + 智能路由 (Day 12-13)
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

---
## Phase 2: 三种 RAG 架构融合

### Day 8: LLM Wiki - 知识编译核心 (Knowledge Compilation) 🔲
- [ ] Wiki 页面数据模型设计（wiki_pages 表、wiki_links 表）
- [ ] Wiki 页面生成服务（LLM 阅读文档 → 提取概念 → 生成结构化 Wiki 页面）
- [ ] 概念提取与去重（实体识别、概念聚类）
- [ ] Wiki 页面存储（PostgreSQL + 向量索引）
- [ ] Wiki 页面语义检索（基于 Embedding 的相似度搜索）
- [ ] 前端：Wiki 页面浏览与搜索界面
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 实现文档 → Wiki 页面的自动编译生成和语义检索

### Day 9: LLM Wiki - 一致性与维护 (Consistency & Maintenance) 🔲
- [ ] Wiki ↔ 原文一致性检查（自动比对、偏差检测）
- [ ] 交叉引用与链接（Wiki 页面之间的概念关联）
- [ ] Wiki 页面版本管理（编辑历史、diff 对比）
- [ ] 文档更新 → Wiki 增量更新机制
- [ ] 自动冲突标注与人工审核队列
- [ ] 前端：Wiki 编辑、版本对比、冲突标注界面
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 建立知识体系的动态维护能力，控制纠偏成本

### Day 10: GraphRAG - 知识图谱构建 (Knowledge Graph Construction) 🔲
- [ ] 实体抽取服务（LLM 从文档中抽取实体和关系）
- [ ] 图数据模型设计（节点、边、属性）
- [ ] 图存储（PostgreSQL + 邻接表 / 可选 Neo4j）
- [ ] 实体消歧与合并（同名实体统一、别名处理）
- [ ] 社区检测与社区摘要（实体聚类 → 高层概念）
- [ ] 图谱可视化 API
- [ ] 前端：知识图谱可视化浏览界面
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 构建文档的知识图谱，支持结构化关系表达

### Day 11: GraphRAG - 图检索与多跳推理 (Graph Retrieval & Reasoning) 🔲
- [ ] 图遍历查询（BFS/DFS 从实体出发检索关联知识）
- [ ] 多跳推理（沿关系路径推导，支持 2-3 跳）
- [ ] 子图提取与上下文构建（将图路径转化为 LLM 可理解的文本）
- [ ] 混合图+向量检索（先图定位实体，再向量扩展上下文）
- [ ] 图增强的答案生成（将关系路径融入 prompt）
- [ ] 前端：推理路径展示（可视化推理链路）
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 实现基于知识图谱的多跳推理和关系查询

### Day 12: 智能路由 - 统一入口 (Intelligent Router) 🔲
- [ ] 查询分析器（LLM 分析问题类型、意图、所需知识深度）
- [ ] 路由策略设计（规则 + LLM 混合路由决策）
- [ ] 路由到传统 RAG / LLM Wiki / GraphRAG 的适配层
- [ ] 结果融合器（多路结果合并、去重、重排序）
- [ ] 路由性能监控（每种 RAG 的响应时间、准确率统计）
- [ ] 前端：统一问答界面（自动路由，展示使用了哪种 RAG）
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 用户无感知地使用最佳 RAG 策略获得答案

### Day 13: 集成与对比仪表盘 (Integration & Comparison Dashboard) 🔲
- [ ] 统一前端界面（整合三种 RAG + 路由的完整 UI）
- [ ] 对比模式（同一问题同时展示三种 RAG 的答案，便于对比）
- [ ] 性能对比仪表盘（延迟、准确率、Token 消耗对比）
- [ ] 成本/收益分析面板
- [ ] 端到端集成测试
- [ ] 完整文档（README 中英文 + 架构图）
- [ ] Docker Compose 完整部署配置
- [ ] 文档：CHANGES.md 核心修改说明
- **Status:** pending
- **Goal:** 提供完整的三架构融合系统，支持效果对比和评估

## Key Questions
1. ~~技术栈选择？~~ → 已确认：Python/FastAPI + React/TS + pgvector
2. 每个阶段的验收标准是什么？ → 见各阶段 Goal
3. 如何保证每个阶段独立可运行？ → 独立目录 + 完整依赖
4. 代码注释格式？ → 双语注释（英文+中文）
5. GraphRAG 图存储方案？ → 优先 PostgreSQL 邻接表（保持技术栈一致），可选 Neo4j
6. 智能路由策略？ → LLM 意图分析 + 规则兜底的混合路由
7. 三种 RAG 如何共享基础设施？ → 共用 pgvector 向量库 + PostgreSQL，各自独立的检索逻辑

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 pgvector 而非独立向量库 | 用户选择，运维简单，支持混合检索 |
| OpenAI 兼容接口 | 灵活切换不同模型供应商 |
| 分阶段独立目录 | 便于学习，每阶段完整可运行 |
| 双语代码注释 | 便于中英文用户学习 |
| GraphRAG 用 PostgreSQL 邻接表而非 Neo4j | 保持技术栈统一，降低学习复杂度 |
| LLM Wiki 纠偏采用"周期性+人工审核"策略 | 实时纠偏成本过高，参考 user_req.md 分析 |
| 智能路由采用 LLM + 规则混合策略 | 纯 LLM 路由有延迟和成本，规则兜底保证可靠性 |
| Day 13 对比模式同时展示三种 RAG 结果 | 便于学习理解各架构优劣 |

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
├── day2/                          # 数据预处理增强
├── day3/                          # 检索优化
├── day4/                          # 生成增强
├── day5/                          # 评估与监控
├── day6/                          # 安全与治理
├── day7/                          # 生产优化
├── day8/                          # LLM Wiki - 知识编译核心
│   ├── backend/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   ├── wiki.py        # Wiki 页面 API
│   │   │   │   └── ...
│   │   │   ├── services/
│   │   │   │   ├── wiki_generator.py   # Wiki 页面生成
│   │   │   │   ├── wiki_store.py       # Wiki 存储
│   │   │   │   ├── concept_extractor.py # 概念提取
│   │   │   │   └── ...
│   │   │   └── models/
│   │   │       ├── database.py    # Wiki 数据表模型
│   │   │       └── schemas.py
│   │   └── test/
│   └── frontend/
│       └── src/
│           ├── components/
│           │   ├── WikiBrowser.tsx    # Wiki 浏览器
│           │   └── ...
│           └── ...
├── day9/                          # LLM Wiki - 一致性与维护
│   └── backend/src/services/
│       ├── wiki_consistency.py    # 一致性检查
│       ├── wiki_versioning.py     # 版本管理
│       └── wiki_updater.py        # 增量更新
├── day10/                         # GraphRAG - 知识图谱构建
│   ├── backend/
│   │   └── src/
│   │       ├── services/
│   │       │   ├── entity_extractor.py  # 实体抽取
│   │       │   ├── relation_extractor.py # 关系抽取
│   │       │   ├── graph_store.py       # 图存储
│   │       │   ├── entity_resolver.py   # 实体消歧
│   │       │   └── community_detector.py # 社区检测
│   │       └── models/
│   │           └── graph_models.py      # 图数据模型
│   └── frontend/
│       └── src/components/
│           └── GraphViewer.tsx          # 图谱可视化
├── day11/                         # GraphRAG - 图检索与推理
│   └── backend/src/services/
│       ├── graph_traversal.py     # 图遍历查询
│       ├── multi_hop_reasoning.py # 多跳推理
│       ├── subgraph_extractor.py  # 子图提取
│       └── graph_rag_service.py   # 图增强 RAG 服务
├── day12/                         # 智能路由 - 统一入口
│   └── backend/src/
│       ├── services/
│       │   ├── query_analyzer.py  # 查询分析器
│       │   ├── router_service.py  # 路由策略
│       │   └── result_fuser.py    # 结果融合
│       └── routers/
│           └── unified_chat.py    # 统一问答入口
├── day13/                         # 集成与对比仪表盘
│   ├── backend/
│   └── frontend/
│       └── src/components/
│           ├── ComparisonView.tsx     # 三架构对比
│           ├── PerformanceDashboard.tsx # 性能仪表盘
│           └── CostAnalysis.tsx       # 成本分析
├── requirement.md
├── user_req.md                    # 用户需求（三种 RAG 对比）
├── task_plan.md
├── findings.md
├── progress.md
├── readme.md
└── readme_cn.md
```

## Notes
- 每个阶段都是完整可运行的独立项目
- 后续阶段在前一阶段基础上增量添加功能
- 所有代码注释使用双语格式：英文在上，中文在下
- 每阶段完成后需要验证端到端功能
