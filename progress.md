# Progress Log
<!--
  WHAT: RAG 项目的进度日志
  WHY: 记录每个阶段的详细进展
  WHEN: 每个阶段完成或有重要进展时更新
-->

## Session: 2026-04-25 (Day 6/Day 7 Chat 标签切换丢失会话状态)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-25
- Bug 报告: Day 6 前端从标签"Chat/问答"切换到其他标签之后再切换回来，原来的会话记录消失了
- 根本原因: `App.tsx` 中 ChatInterface 使用条件渲染 `{activeTab === 'chat' && <ChatInterface />}`，当 activeTab 不是 'chat' 时组件被卸载，其内部 state（messages、conversationId 等）全部丢失。切回来时重新创建新实例，状态初始化为空
- 修复方案: 将 ChatInterface 的渲染方式从条件渲染改为 CSS 隐藏（`display: none`），保持组件始终挂载，状态在标签切换时得以保留
- Actions taken:
  - **Day 6** (`frontend/src/App.tsx`): 将条件渲染改为 `<div className={activeTab !== 'chat' ? 'hidden' : ''}>` 包裹
  - **Day 7** (`frontend/src/App.tsx`): 同上修复
- Files modified:
  - day6/frontend/src/App.tsx
  - day7/frontend/src/App.tsx

---

## Session: 2026-04-25 (Day 6/Day 7 前端 API 客户端缺少 JWT token)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-25
- Bug 报告: 进入审计页面时，前端报 "Failed to load audit data"，后端返回 401 Unauthorized
- 错误日志: `GET /audit/logs?limit=100` 和 `GET /audit/summary?days=7` 均返回 401
- 根本原因: Day 6 前端的 `client.ts` 创建了 axios 实例，但**没有请求拦截器**将 localStorage 中的 JWT token 附加到 `Authorization` header。LoginPanel 成功存储了 `auth_token`，但后续所有 API 请求都没有携带它。后端 `get_current_user` 依赖发现 Authorization header 缺失，直接返回 401。
- 额外发现: `askQuestionStream` 使用原生 `fetch()` 而非 axios，同样不会自动携带 token
- 影响范围: 这不仅影响 audit 端点，理论上所有使用 `Depends(get_current_user)` 或 `Depends(require_role(...))` 的后端端点都会受影响。documents 和 chat 端点恰好没有认证依赖所以没暴露问题。
- 修复方案:
  1. 在 axios 实例上添加 `request interceptor`，从 localStorage 读取 `auth_token` 并设置 `Authorization: Bearer <token>` header
  2. 添加 `response interceptor`，当收到 401 响应时清除过期凭据并强制重新登录
  3. 在 `askQuestionStream` 的 `fetch()` 调用中手动添加 `Authorization` header
- Actions taken:
  - **Day 6** (`frontend/src/api/client.ts`): 添加 axios 请求/响应拦截器 + 修复 fetch() Authorization header
  - **Day 7** (`frontend/src/api/client.ts`): 同上
- Files modified:
  - day6/frontend/src/api/client.ts
  - day7/frontend/src/api/client.ts

---

## Session: 2026-04-12 (Day 1-7 vector_store 表存在性检查优化)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-12
- Bug 报告: `vector_store.py` 的 `connect` 方法使用 `try/except ProgrammingError: pass` 处理表已存在的情况，会吞掉所有 ProgrammingError（权限不足、连接断开等），不利于排查问题
- 根本原因: PGEngine 的 `ainit_vectorstore_table` 使用 `CREATE TABLE`（不带 `IF NOT EXISTS`），表存在时抛异常；原代码无差别地忽略所有 ProgrammingError
- 修复方案:
  - 使用 `self._async_engine`（运行在 FastAPI 事件循环中）查询 `pg_tables` 检查表是否存在
  - 不存在时才调用 `ainit_vectorstore_table`
  - Day 1-2: 新增 `_async_engine` 属性及生命周期管理（connect/disconnect）
  - Day 3-7: 复用已有的 `_async_engine`
  - 移除 `ProgrammingError` import（不再需要异常捕获）
- 技术要点: PGEngine 内部使用独立的事件循环（`_default_loop`），直接访问 `_pool.connect()` 会导致 "Future attached to a different loop" 错误。必须使用在 FastAPI 事件循环中创建的 `AsyncEngine`（通过 `create_async_engine`）
- Actions taken:
  - **Day 1-2** (`vector_store.py`): 添加 `_async_engine`；替换 try/except 为 `pg_tables` 查询；disconnect 中添加 `_async_engine.dispose()`
  - **Day 3-5** (`vector_store.py`): 替换 try/except 为 `pg_tables` 查询；移除 `ProgrammingError` import
  - **Day 6-7** (`vector_store.py`): 替换 try/except 为 `pg_tables` 查询；移除 `ProgrammingError` import
- Files modified:
  - day1-day7/backend/src/services/vector_store.py

---

## Session: 2026-04-12 (Day 1-7 health_check 端点修复)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-12
- Bug 报告: `health_check` 端点存在 4 个问题:
  1. `status` 硬编码为 "healthy"，即使连接断开也返回健康
  2. 仅检查 vector_store，不检查 db_service
  3. 访问私有属性 `vector_store._vectorstore`
  4. 没有实际的连接存活测试
- 根本原因: 健康检查端点仅做了简单的属性空值检查，没有实际验证数据库连接是否存活
- 修复方案:
  - 在 `database_service.py` 添加 `health_check()` 方法，执行 `SELECT 1` 验证连接
  - 在 `vector_store.py` 添加 `health_check()` 方法，检查 `_vectorstore` 是否已初始化
  - 重写 `main.py` 中的 `health_check` 端点：
    - 调用 `db_service.health_check()` 和 `vector_store.health_check()` 进行实际存活检查
    - 根据检查结果返回 "healthy" 或 "unhealthy"
    - 不健康时返回 HTTP 503
    - 添加 `from fastapi import Response` 以设置状态码
  - Day 6/7: 将 `audit_service.get_logs` 调用包裹在 try/except 中，防止审计日志查询失败导致健康检查崩溃
  - Day 7: 修复 `day=6` 硬编码为 `day=7`
- Actions taken:
  - **Day 1** (`database_service.py`): 添加 `health_check()` 方法
  - **Day 1** (`vector_store.py`): 添加 `health_check()` 方法
  - **Day 1** (`main.py`): 重写健康检查端点
  - **Day 2-5**: 同 Day 1 修改，Day 3-5 额外保留 BM25 索引状态检查（信息性）
  - **Day 6-7**: 同 Day 3-5 修改，额外将 `audit_service.get_logs` 包裹在 try/except 中
- 额外修改: HealthResponse 字段从 `database: str` 拆分为 `db_status: str` + `vector_status: str`，分别展示两个服务的独立状态
- 额外修改: Day 4/5 `version` 和 `day` 值从错误的 `"3.0.0"/3` 修正为正确的 `"4.0.0"/4` 和 `"5.0.0"/5`
- Files modified:
  - day1-day7/backend/src/services/database_service.py (添加 health_check 方法)
  - day1-day7/backend/src/services/vector_store.py (添加 health_check 方法)
  - day1-day7/backend/src/main.py (重写健康检查端点)
  - day1-day7/backend/src/models/schemas.py (HealthResponse 字段拆分)

---

## Session: 2026-04-12 (Day 1-7 文档删除失败修复)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-12
- Bug 报告: `delete_document` 使用 `filter={"filename": document_id}` 删除文档，但 `document_id` 是 UUID（store_document 返回的第一个 chunk ID），而 `filename` 存储的是原始文件名，导致过滤器永远匹配不到任何文档
- 根本原因: `store_document` 返回 PGVector 生成的第一个 chunk UUID，`delete_document` 却用这个 UUID 去匹配 `filename` 字段
- 修复方案:
  - 在 `store_document` 中使用 `uuid.uuid4()` 生成独立的 `doc_id`
  - 将 `doc_id` 添加到每个 chunk 的 metadata 中
  - `store_document` 返回 `doc_id` 而非 `ids[0]`
  - `delete_document` 改为 `filter={"doc_id": document_id}`
- Actions taken:
  - **Day 1** (`vector_store.py`): 添加 `import uuid`；`store_document` 生成 `doc_id` 并写入 metadata；`delete_document` 使用 `doc_id` 过滤
  - **Day 2** (`vector_store.py`): 同上
  - **Day 3** (`vector_store.py`): 同上
  - **Day 4** (`vector_store.py`): 同上
  - **Day 5** (`vector_store.py`): 同上
  - **Day 6** (`vector_store.py`): 同上
  - **Day 7** (`vector_store.py`): 同上
- 注意事项:
  - 已在数据库中存在的旧文档（没有 `doc_id` metadata）无法通过新逻辑删除
  - 不影响 router 或 registry 代码（接口签名不变）
  - `get_all_documents_for_bm25` 无需修改（它读 `filename` 不读 `doc_id`）
- Files modified:
  - day1-day7/backend/src/services/vector_store.py (修复 store_document 和 delete_document)

---

## Session: 2026-04-11 (Day 1-5 数据库迁移到 SQLAlchemy ORM)

### 数据库迁移重构
- **Status:** complete
- **Started:** 2026-04-11
- 需求: 将 Day 6 的 SQLAlchemy ORM 统一数据库存储方式应用到 Day 1-5
- Actions taken:
  - **Day 1:**
    - 新增 `models/database.py`（DocumentRegistry: id=String(255), filename, chunk_count, created_at）
    - 新增 `services/database_service.py`
    - 重写 `services/document_registry.py` 使用 ORM
    - 更新 `main.py` 添加 db_service 初始化
    - 更新 `pyproject.toml` 添加 sqlalchemy
  - **Day 2-4（共享代码）:**
    - 新增 `models/database.py`（DocumentRegistry 含 file_type, file_size, title）
    - 新增 `services/database_service.py`
    - 重写 `services/document_registry.py` 使用 ORM
    - 更各天 `main.py` 和 `pyproject.toml`
  - **Day 5:**
    - 同 Day 2-4，额外新增 QAHistory 模型（confidence=Float）
    - 重写 `services/qa_history_service.py` 使用 ORM
  - **设计决策:**
    - 保持 VARCHAR(255) 主键（不改为 UUID）
    - QAHistory confidence 保持 Float（不改为 Integer）
    - rag_documents 表不动（仍由 LangChain PGVector 管理）
    - vector_store.py 的 BM25 方法不动（直接查 rag_documents 表）
- Files created: day1-day5 models/database.py, services/database_service.py
- Files modified: day1-day5 services/document_registry.py, main.py, pyproject.toml; day5 services/qa_history_service.py
- Docs updated: day2-day5 CHANGES.md, progress.md

---

## Session: 2026-04-11 (Day 6/Day 7 数据库迁移到 SQLAlchemy ORM)

### 数据库迁移重构
- **Status:** complete
- **Started:** 2026-04-11
- 需求: 将用户和登录记录的存储方式从 JSON 文件修改为 PostgreSQL 数据库存储
- 扩展需求: 统一所有数据库存储方式为 SQLAlchemy ORM（用户、审计日志、文档注册表、QA 历史）
- Actions taken:
  - **新增数据库模型** (`models/database.py`):
    - `Base`: 所有 ORM 模型的基类（AsyncAttrs + DeclarativeBase）
    - `AppUser`: 用户表（UUID 主键，用户名/邮箱唯一索引）
    - `AuditLog`: 审计日志表（JSONB details 字段）
    - `DocumentRegistry`: 文档注册表（created_at 替代 upload_date）
    - `QAHistory`: 问答历史表（String(36) ID 类型兼容现有表）
  - **新增数据库服务** (`services/database_service.py`):
    - `DatabaseService`: 统一数据库连接和会话管理
    - 使用 asyncpg 驱动（postgresql+asyncpg://）
    - async_sessionmaker 会话工厂
    - connect()/disconnect()/create_tables() 生命周期方法
  - **认证服务重构** (`services/auth_service.py`):
    - 所有方法改为异步（async）
    - JSON 文件存储 → SQLAlchemy ORM
    - 移除 _load_users() 和 _save_users() 方法
    - 使用 select(AppUser).where() 查询
    - session.add() + session.commit() 保存
  - **审计服务重构** (`services/audit_service.py`):
    - 所有方法改为异步
    - JSON 文件存储 → SQLAlchemy ORM
    - JSONB 类型存储 details
  - **文档注册表重构** (`services/document_registry.py`):
    - 原始 SQL → SQLAlchemy ORM
    - 字段名 upload_date → created_at
  - **QA 历史服务重构** (`services/qa_history_service.py`):
    - 原始 SQL → SQLAlchemy ORM
    - 移除 UUID 转换（使用 String(36) 直接查询）
  - **主程序启动流程** (`main.py`):
    - 启动时调用 db_service.connect()
    - 调用 db_service.create_tables() 自动创建表
    - 调用 auth_service._create_default_admin() 创建默认管理员
    - 关闭时调用 db_service.disconnect()
  - **路由文件更新**:
    - `routers/auth.py`: 所有调用添加 await
    - `routers/audit.py`: 所有调用添加 await
    - `routers/permissions.py`: 所有调用添加 await
  - **Day 7 同步**: 所有更改同步到 day7/ 目录
  - **依赖更新**: 添加 sqlalchemy[asyncio]>=2.0.0
  - **Bug 修复**:
    - 修复 auth_service.py 空函数体（添加 pass）
    - 修复 database_service.py SQL 文本包裹（添加 text()）
    - 修复路由 await 缺失（运行时错误）
    - 修复字段名不匹配（upload_date → created_at）
    - 修复 QAHistory ID 类型（UUID → String(36)）
  - **文档更新**:
    - day6/CHANGES.md: 添加"数据库迁移增强"章节
    - day7/CHANGES.md: 添加 Day 6 数据库迁移继承说明
- Files created:
  - day6/backend/src/models/database.py (新增)
  - day6/backend/src/services/database_service.py (新增)
  - day7/backend/src/models/database.py (同步)
  - day7/backend/src/services/database_service.py (同步)
- Files modified:
  - day6/backend/pyproject.toml (添加 sqlalchemy)
  - day6/backend/src/main.py (数据库初始化)
  - day6/backend/src/services/auth_service.py (ORM 重构)
  - day6/backend/src/services/audit_service.py (ORM 重构)
  - day6/backend/src/services/document_registry.py (ORM 重构)
  - day6/backend/src/services/qa_history_service.py (ORM 重构)
  - day6/backend/src/routers/auth.py (添加 await)
  - day6/backend/src/routers/audit.py (添加 await)
  - day6/backend/src/routers/permissions.py (添加 await)
  - day7/backend/pyproject.toml (同步)
  - day7/backend/src/main.py (同步)
  - day7/backend/src/services/* (同步)
  - day7/backend/src/routers/* (同步)
  - day6/CHANGES.md (文档更新)
  - day7/CHANGES.md (文档更新)
- Git commit: `refactor(day6, day7): 统一数据库存储方式为 SQLAlchemy ORM`

---

## Session: 2026-04-10 (Day 7 同步 Day 6 修复 + Day 7 完整功能)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-10
- Bug 报告: Day 7 缺少 Day 6 修复和 Day 7 完整功能
- 根本原因: Day 7 停留在 Day 3-5 阶段，需要同步 Day 6 修复并添加 Day 7 生产优化
- Actions taken:
  - **后端依赖** (`pyproject.toml`):
    - 添加 Day 6 安全依赖: passlib, bcrypt<4.0.0, python-jose, email-validator
    - 添加 Day 7 生产依赖: cachetools, redis, tenacity, prometheus-client
  - **后端模型** (`schemas.py`):
    - 添加 Day 6 认证模型: `UserLoginRequest`, `UserRegisterRequest`, `TokenResponse`, `UserInfo`
    - 添加 Day 6 审计模型: `AuditLogEntry`, `AuditLogListResponse`, `AuditSummaryResponse`
    - 添加 Day 6 权限模型: `PermissionGrantRequest`, `Permission`, `DocumentPermissionsResponse`
  - **后端配置** (`config.py`):
    - 添加 Day 6 安全配置: AUTH_ENABLED, JWT_*, PASSWORD_*, CONTENT_FILTER_*, AUDIT_LOG_*
    - 添加 Day 7 生产配置: CACHE_*, REDIS_*, RETRY_*, METRICS_*, REQUEST_TIMEOUT_*
  - **后端主程序** (`main.py`):
    - 更新为 Day 7 版本 (7.0.0)
    - 导入 Day 6 服务: audit_service
    - 导入 Day 7 服务: cache_service, performance_service
    - 注册 Day 6 路由器: auth, permissions, audit
    - 添加请求计时中间件
    - 添加 /metrics 和 /cache/stats 端点
  - **前端 API** (`client.ts`):
    - 添加 Day 6 认证类型: `UserInfo`, `UserLoginRequest`, `UserRegisterRequest`, `TokenResponse`
    - 添加 Day 6 认证函数: `login()`, `register()`, `logout()`, `getCurrentUser()`
    - 添加 Day 6 用户管理函数: `getUsers()`, `updateUserRole()`, `deactivateUser()`, `activateUser()`
    - 添加 Day 6 审计日志类型和函数: `getAuditLogs()`, `getAuditSummary()`
- Files modified:
  - day7/backend/pyproject.toml (添加 Day 6/7 依赖)
  - day7/backend/src/models/schemas.py (添加 Day 6 模型)
  - day7/backend/src/config.py (添加 Day 6/7 配置)
  - day7/backend/src/main.py (更新为 Day 7 版本)
  - day7/frontend/src/api/client.ts (添加 Day 6 认证 API)

---

## Session: 2026-04-10 (Day 7 额外修复)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-10
- Bug 报告: Day 7 额外缺少的 Day 6 修复和配置参数
- 根本原因: 第二轮检查发现更多需要同步的内容
- Actions taken:
  - **后端路由** (`permissions.py`): 移除重复的 `from services.auth_service import auth_service`
  - **后端配置** (`config.py`): 添加缺失的 Day 7 配置参数
    - `cache_max_size`: 缓存最大大小 (默认 1000)
    - `retry_backoff_factor`: 重试退避因子 (默认 1.0)
    - `retry_max_wait_seconds`: 重试最大等待时间 (默认 10.0)
  - **前端组件** (`LoginPanel.tsx`): 修复角色类型断言
    - `role: response.role as 'admin' | 'user' | 'viewer'`
  - **前端组件** (`UserManagementPanel.tsx`): 修复角色更新调用
    - `await updateUserRole(userId, { role: newRole as 'admin' | 'user' | 'viewer' })`
  - **数据目录**: 创建 `day7/backend/data/` 并复制用户和审计日志文件
- Files modified:
  - day7/backend/src/routers/permissions.py (移除重复导入)
  - day7/backend/src/config.py (添加缺失配置)
  - day7/frontend/src/components/LoginPanel.tsx (类型断言修复)
  - day7/frontend/src/components/UserManagementPanel.tsx (API 调用修复)
  - day7/backend/data/ (新建目录及文件)

---

## Session: 2026-04-10 (Day 6 后端依赖和配置修复)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-10
- Bug 报告: 后端 bcrypt 版本不兼容 + 缺少 Day 6 认证模型
- 根本原因:
  1. bcrypt 5.x 与 passlib 不兼容（passlib 需要 bcrypt 3.x）
  2. Day 6 新增的认证功能需要完整的 Pydantic 模型
  3. main.py 未注册 Day 6 新路由器
- Actions taken:
  - 修复 bcrypt 版本兼容性: 在 `pyproject.toml` 中添加 `bcrypt<4.0.0` 约束
  - 添加完整的 Day 6 认证模型到 `schemas.py`:
    - `UserLoginRequest`, `UserRegisterRequest`, `TokenResponse`
    - `UserInfo`, `UserListResponse`, `UserRoleUpdateRequest`
    - `AuditLogEntry`, `AuditLogListResponse`, `AuditSummaryResponse`
    - `PermissionGrantRequest`, `Permission`, `DocumentPermissionsResponse`
  - 更新 `config.py` 添加 Day 6 安全配置参数
  - 更新 `main.py` 注册 Day 6 路由器 (auth, permissions, audit)
  - 修复 `permissions.py` 重复导入问题
  - 前端构建验证通过（无错误）
- Files modified:
  - day6/backend/pyproject.toml (修复 bcrypt 版本约束)
  - day6/backend/src/models/schemas.py (添加 Day 6 认证、权限、审计模型)
  - day6/backend/src/config.py (添加 AUTH_ENABLED, JWT_*, PASSWORD_* 等配置)
  - day6/backend/src/main.py (注册 auth, permissions, audit 路由器)
  - day6/backend/src/routers/permissions.py (移除重复导入)

---

## Session: 2026-04-09 (Day 6 前端 API 缺失修复)

### Bug 修复
- **Status:** complete
- **Started:** 2026-04-09
- Bug 报告: `LoginPanel.tsx` 导入错误 - `client.ts` 没有导出 `login`, `register`, `UserInfo`
- 根本原因: Day 6 新增的认证、用户管理、审计日志功能后端已完成，但前端 API 客户端缺少对应类型和函数
- Actions taken:
  - 添加认证相关类型: `UserInfo`, `UserLoginRequest`, `UserRegisterRequest`, `TokenResponse`
  - 添加认证 API 函数: `login()`, `register()`, `logout()`, `getCurrentUser()`
  - 添加用户管理类型: `UserListResponse`, `UserRoleUpdateRequest`
  - 添加用户管理函数: `getUsers()`, `updateUserRole()`, `deactivateUser()`, `activateUser()`
  - 添加审计日志类型: `AuditLogEntry`, `AuditLogListResponse`, `AuditSummaryResponse`
  - 添加审计日志函数: `getAuditLogs()`, `getAuditSummary()`
  - 修复 LoginPanel.tsx 中的角色类型断言
  - 修复 UserManagementPanel.tsx 中的角色更新请求参数
- Files modified:
  - day6/frontend/src/api/client.ts (添加 Day 6 认证、用户管理、审计 API)
  - day6/frontend/src/components/LoginPanel.tsx (修复类型断言)
  - day6/frontend/src/components/UserManagementPanel.tsx (修复 API 调用)

---

## Session: 2026-04-04 (Day 5 评估功能修复)

### Bug 修复阶段
- **Status:** complete
- **Started:** 2026-04-04
- Actions taken:
  - 修复 evaluation 路由未注册问题 (404 Not Found)
  - 添加缺失依赖：ragas, datasets, opentelemetry-api, opentelemetry-sdk, structlog
  - 修复 .env 文件加载路径问题
  - 适配 ragas 0.4.x API 变更：
    - 使用 LangchainLLMWrapper 和 LangchainEmbeddingsWrapper
    - 设置 answer_relevancy.strictness=1 (兼容通义千问 API)
    - 更新数据集列名 (user_input, response, retrieved_contexts, reference)
    - 使用 result.to_pandas() 提取评估结果
- Files modified:
  - day5/backend/src/main.py (注册 evaluation 路由器)
  - day5/backend/pyproject.toml (添加依赖)
  - day5/backend/src/config.py (修复 .env 加载路径)
  - day5/backend/src/services/evaluation_service.py (适配 ragas 0.4.x)
  - day5/backend/uv.lock (锁定依赖版本)

---

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
  - 增强全项目统一日志系统（day1-day7）
    - config.py: 添加 setup_logging() 和 get_logger() 函数
    - main.py: 初始化日志系统，print → logger
    - routers/chat.py: 使用 get_logger(__name__)
    - services/*.py: 所有 print 替换为 logger
    - 支持环境变量 LOG_LEVEL 控制日志级别
    - 第三方库日志降噪（httpx, httpcore, urllib3, asyncio）
- Files created/modified:
  - day1-day7/backend/src/config.py (添加日志函数)
  - day1-day7/backend/src/main.py (初始化日志)
  - day1-day7/backend/src/routers/chat.py (使用 get_logger)
  - day1-day7/backend/src/services/document_registry.py (新增)
  - day1-day7/backend/src/services/vector_store.py (修改)
  - day3-day7/backend/src/services/retrieval_service.py (添加 jieba)
  - day3-day7/backend/pyproject.toml (添加 jieba 依赖)
  - day4-day7/backend/src/services/citation_service.py (修复 findall→finditer)
  - day4-day7/.vscode/settings.json (新增)
  - day3/CHANGES.md (更新文档)
  - progress.md (更新进度)

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
| Where am I? | Phase 1 (传统 RAG Day 1-7) 已完成，Phase 2 (三架构融合 Day 8-13) 待启动 |
| Where am I going? | Day 8: LLM Wiki 知识编译核心 |
| What's the goal? | 在传统 RAG 基础上，新增 LLM Wiki 和 GraphRAG，最终通过智能路由统一入口 |
| What have I learned? | 传统 RAG 全流程已完成；三种 RAG 优劣对比已分析（见 findings.md Phase 2） |
| What have I done? | Day 1-7 传统 RAG 全部完成；Phase 2 规划文件已更新 |

## Next Actions
<!--
  下一步行动项
-->
1. **Day 8**: LLM Wiki 知识编译核心 — Wiki 页面数据模型 + 生成服务 + 语义检索
2. **Day 9**: LLM Wiki 一致性与维护 — 一致性检查 + 交叉引用 + 版本管理
3. **Day 10**: GraphRAG 知识图谱构建 — 实体/关系抽取 + 图存储 + 社区检测
4. **Day 11**: GraphRAG 图检索与推理 — 图遍历 + 多跳推理 + 子图提取
5. **Day 12**: 智能路由统一入口 — 查询分析 + 路由策略 + 结果融合
6. **Day 13**: 集成与对比仪表盘 — 统一 UI + 三架构对比 + 成本分析

## Daily Progress Plan (Phase 2)
<!--
  Phase 2 每日计划
-->
| Day | Plan | Status | Key Deliverables |
|-----|------|--------|------------------|
| Day 8 | LLM Wiki - 知识编译核心 | pending | Wiki 生成 + 存储 + 检索 |
| Day 9 | LLM Wiki - 一致性与维护 | pending | 一致性检查 + 版本管理 + 增量更新 |
| Day 10 | GraphRAG - 知识图谱构建 | pending | 实体/关系抽取 + 图存储 + 可视化 |
| Day 11 | GraphRAG - 图检索与推理 | pending | 图遍历 + 多跳推理 + 路径可视化 |
| Day 12 | 智能路由 - 统一入口 | pending | 查询分析 + LLM 路由 + 结果融合 |
| Day 13 | 集成与对比仪表盘 | pending | 统一 UI + 对比模式 + 部署配置 |

---
*Update after completing each phase or encountering errors*
