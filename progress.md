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

## Daily Progress Plan
<!--
  每日计划与实际进度对比
-->

| Day | Plan | Status | Key Deliverables |
|-----|------|--------|------------------|
| Day 1 | 最小化 RAG | pending | 文档上传 + 问答 |
| Day 2 | 数据预处理增强 | pending | 多格式解析 + 智能分块 |
| Day 3 | 检索优化 | pending | 混合检索 + 重排序 |
| Day 4 | 生成增强 | pending | 引用溯源 + 流式输出 |
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
| Where am I? | Phase 1: 技术栈确认与规划 |
| Where am I going? | Phase 2: Day 1 最小化 RAG 实现 |
| What's the goal? | 创建分阶段 RAG 教程项目，从核心功能到完整系统 |
| What have I learned? | 见 findings.md |
| What have I done? | 确认技术栈，创建规划文件 |

## Next Actions
<!--
  下一步行动项
-->
1. 等待用户确认规划方案
2. 开始 Day 1 实现：
   - 创建 day1 目录结构
   - 实现后端 FastAPI 基础框架
   - 实现文档上传和分块
   - 实现向量存储和检索
   - 实现问答 API
   - 实现前端界面
   - 端到端测试

---
*Update after completing each phase or encountering errors*
