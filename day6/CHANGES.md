# Day 6 核心修改文档 / Day 6 Core Changes Documentation

本文档列出了 Day 6 相对于 Day 5 的核心修改及其原因。
This document lists the core changes from Day 5 to Day 6 and the reasons behind them.

---

## 1. 新增文件 / New Files

### `backend/src/services/auth_service.py`

**功能 / Purpose:**
JWT 用户认证服务，支持用户注册、登录和令牌管理。

**为什么新增 / Why Added:**
- Day 5 没有用户认证功能
- Day 6 需要支持安全的企业级访问控制
- 提供 JWT token 生成和验证

**核心类 / Core Classes:**
```python
@dataclass
class User:
    """User model for authentication / 认证用户模型"""
    id: str
    username: str
    email: str
    hashed_password: str
    role: str = "user"  # "admin", "user", "viewer"
    is_active: bool = True

class AuthService:
    """Authentication service / 认证服务"""
    def hash_password(self, password: str) -> str
    def verify_password(self, plain_password: str, hashed_password: str) -> bool
    def create_access_token(self, user: User) -> str
    def decode_token(self, token: str) -> Optional[TokenData]
    def register_user(self, username, email, password, role) -> User
    def authenticate_user(self, username: str, password: str) -> Optional[User]
```

---

### `backend/src/services/permission_service.py`

**功能 / Purpose:**
文档级权限控制（ACL）服务。

**为什么新增 / Why Added:**
- Day 5 没有权限控制
- Day 6 需要细粒度的文档访问控制
- 支持基于角色的默认权限

**核心类 / Core Classes:**
```python
class Permission(Enum):
    """Permission levels / 权限级别"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class PermissionService:
    """Permission management service / 权限管理服务"""
    def grant_permission(self, document_id, user_id, permission, granted_by) -> DocumentPermission
    def revoke_permission(self, document_id, user_id) -> bool
    def check_permission(self, document_id, user_id, required_permission, user_role) -> bool
    def get_document_permissions(self, document_id) -> List[DocumentPermission]
```

---

### `backend/src/services/audit_service.py`

**功能 / Purpose:**
审计日志服务，记录用户操作。

**为什么新增 / Why Added:**
- Day 5 没有审计追踪
- Day 6 需要合规性审计支持
- 提供安全事件追溯能力

**核心类 / Core Classes:**
```python
class AuditAction(Enum):
    """Audit action types / 审计操作类型"""
    LOGIN, LOGOUT, LOGIN_FAILED = ...
    USER_CREATE, USER_UPDATE, USER_DEACTIVATE = ...
    DOCUMENT_UPLOAD, DOCUMENT_DELETE, DOCUMENT_VIEW = ...
    PERMISSION_GRANT, PERMISSION_REVOKE = ...

class AuditService:
    """Audit logging service / 审计日志服务"""
    def log_action(self, action, user_id, username, resource_type, ...) -> AuditLog
    def log_login(self, user_id, username, ip_address, success) -> AuditLog
    def log_document_action(self, action, user_id, username, document_id, ...) -> AuditLog
    def get_logs(self, user_id, action, resource_type, ...) -> List[AuditLog]
    def get_user_activity_summary(self, user_id, days) -> Dict
    def get_system_activity_summary(self, days) -> Dict
    def export_logs(self, format, start_date, end_date) -> str
```

---

### `backend/src/services/content_filter_service.py`

**功能 / Purpose:**
内容过滤服务，检测和阻止恶意输入。

**为什么新增 / Why Added:**
- Day 5 没有输入验证
- Day 6 需要防止注入攻击
- 保护系统免受恶意输入

**核心类 / Core Classes:**
```python
class ContentFilterService:
    """Content filtering and validation service / 内容过滤和验证服务"""
    def filter_input(self, content, check_sql_injection, check_xss, ...) -> ContentFilterResponse
    def filter_output(self, content, check_pii, check_inappropriate) -> ContentFilterResponse
    def sanitize_html(self, content: str) -> str
    def truncate_content(self, content, max_length) -> str
```

**检测能力 / Detection Capabilities:**
- SQL 注入检测
- XSS 攻击检测
- 提示注入检测（AI 输入）
- PII 数据检测和遮罩
- 不当内容检测

---

### `backend/src/routers/auth.py`

**功能 / Purpose:**
认证和用户管理 API 路由。

**新增端点 / New Endpoints:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Get current user info
- `GET /auth/users` - List users (admin)
- `PUT /auth/users/{user_id}/role` - Update user role (admin)
- `POST /auth/users/{user_id}/deactivate` - Deactivate user (admin)

---

### `backend/src/routers/permissions.py`

**功能 / Purpose:**
权限管理 API 路由。

**新增端点 / New Endpoints:**
- `POST /permissions/grant` - Grant permission
- `DELETE /permissions/revoke/{document_id}/{user_id}` - Revoke permission
- `GET /permissions/document/{document_id}` - Get document permissions
- `GET /permissions/user/{user_id}` - Get user permissions
- `GET /permissions/check/{document_id}` - Check user permission

---

### `backend/src/routers/audit.py`

**功能 / Purpose:**
审计日志 API 路由。

**新增端点 / New Endpoints:**
- `GET /audit/logs` - Get audit logs (admin)
- `GET /audit/user/{user_id}/activity` - Get user activity (admin)
- `GET /audit/summary` - Get system activity summary (admin)
- `GET /audit/my-activity` - Get current user's activity
- `GET /audit/export` - Export audit logs
- `GET /audit/actions` - Get available action types

---

## 2. 修改的文件 / Modified Files

### `backend/src/config.py`

**修改内容 / Changes:**

```python
class Settings:
    # ... existing settings ...

+   # Security Configuration (Day 6)
+   # 安全配置（Day 6）
+   jwt_secret_key: str
+   jwt_algorithm: str = "HS256"
+   jwt_expiration_hours: int = 24
+   password_min_length: int = 8
+   auth_enabled: bool = True
+   audit_enabled: bool = True
+   content_filter_enabled: bool = True
+   audit_log_retention_days: int = 90
+   max_login_attempts: int = 5
```

---

### `backend/src/models/schemas.py`

**新增模型 / New Models:**

- `UserRegisterRequest` - User registration request
- `UserLoginRequest` - User login request
- `TokenResponse` - JWT token response
- `UserInfo` - User information
- `UserListResponse` - User list response
- `UserRoleUpdateRequest` - Role update request
- `PermissionGrantRequest` - Permission grant request
- `PermissionInfo` - Permission information
- `DocumentPermissionsResponse` - Document permissions
- `AuditLogEntry` - Audit log entry
- `AuditLogListResponse` - Audit log list
- `AuditSummaryResponse` - Audit summary
- `ContentFilterResult` - Filter check result
- `ContentFilterResponse` - Filter response

**修改模型 / Modified Models:**

```python
class HealthResponse(BaseModel):
    version: str = "6.0.0"
    day: int = 6
+   auth_enabled: bool = True
+   audit_enabled: bool = True
+   content_filter_enabled: bool = True
```

---

### `backend/src/main.py`

**修改内容 / Changes:**
- 更新版本到 6.0.0
- 导入新的路由和服务
- 添加认证、权限、审计路由
- 更新 API 描述
- 添加默认凭据信息

---

### `backend/pyproject.toml`

**新增依赖 / Added Dependencies:**

```toml
# Security & Governance (Day 6)
# 安全与治理（Day 6）
"PyJWT>=2.8.0",               # JWT authentication
"passlib[bcrypt]>=1.7.4",     # Password hashing
"python-jose[cryptography]>=3.3.0",  # Enhanced JWT
"email-validator>=2.1.0",     # Email validation
```

---

## 3. 前端变更 / Frontend Changes

### `frontend/src/api/client.ts`

**新增内容 / Added Content:**
- Auth token 拦截器
- Day 6 类型定义（认证、权限、审计）
- Day 6 API 函数（登录、注册、权限、审计）

### `frontend/src/components/LoginPanel.tsx` (NEW)

**功能 / Purpose:**
登录和注册界面组件。

### `frontend/src/components/AuditPanel.tsx` (NEW)

**功能 / Purpose:**
审计日志界面组件，显示系统活动摘要和日志列表。

### `frontend/src/App.tsx`

**修改内容 / Changes:**
- 添加认证状态管理
- 集成 LoginPanel 组件
- 添加 AuditPanel 标签页（仅管理员）
- 显示当前用户信息
- 添加登出功能

### `frontend/package.json`

**修改内容 / Changes:**
- 版本更新到 6.0.0
- 描述更新为 Day 6

---

## 4. 安全特性总结 / Security Features Summary

### 认证 / Authentication
| 特性 | 描述 |
|------|------|
| JWT Token | 基于令牌的无状态认证 |
| 密码哈希 | bcrypt 哈希算法 |
| Token 过期 | 可配置的过期时间 |
| 自动登出 | 401 响应自动清除 token |

### 权限 / Permissions
| 角色 | 权限 |
|------|------|
| admin | 完全访问、用户管理、权限管理 |
| user | 读写文档、查看审计日志 |
| viewer | 只读文档 |

### 审计 / Audit
| 操作类型 | 记录内容 |
|----------|----------|
| 认证 | 登录、登出、失败尝试 |
| 用户 | 创建、更新、停用 |
| 文档 | 上传、删除、查看 |
| 权限 | 授予、撤销 |

### 内容过滤 / Content Filtering
| 检测类型 | 处理方式 |
|----------|----------|
| SQL 注入 | 阻止 |
| XSS | 阻止 |
| 提示注入 | 警告 |
| PII | 遮罩 |

---

## 5. 默认凭据 / Default Credentials

开发环境默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`

**警告 / Warning:** 生产环境必须更改默认密码！

---

## 6. 数据库迁移增强 / Database Migration Enhancement (Post-Release Update)

### 概述 / Overview

**重要更新 / Important Update:** Day 6 已完成从 JSON 文件存储到 PostgreSQL 数据库的完整迁移。
**Important Update:** Day 6 has completed full migration from JSON file storage to PostgreSQL database.

这次迁移统一了所有数据存储方式，使用 SQLAlchemy ORM 替代原始 SQL 和 JSON 文件。
This migration unified all data storage methods, using SQLAlchemy ORM instead of raw SQL and JSON files.

---

### 新增文件 / New Files

### `backend/src/models/database.py`

**功能 / Purpose:**
统一的数据库模型定义，使用 SQLAlchemy ORM。

**为什么新增 / Why Added:**
- 统一管理所有数据库表结构
- 提供类型安全的 ORM 模型
- 支持异步数据库操作

**核心模型 / Core Models:**
```python
class Base(AsyncAttrs, DeclarativeBase):
    """所有数据库模型的基类 / Base class for all database models"""

class AppUser(Base):
    """用户表 / User table"""
    __tablename__ = "app_users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class AuditLog(Base):
    """审计日志表 / Audit log table"""
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50))
    user_id = Column(UUID(as_uuid=True))
    username = Column(String(50))
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB, default=dict)
    status = Column(String(20), default="success")

class DocumentRegistry(Base):
    """文档注册表 / Document registry table"""
    __tablename__ = "document_registry"
    id = Column(UUID(as_uuid=True), primary_key=True)
    filename = Column(String(255), unique=True, nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    chunk_count = Column(Integer, default=0)

class QAHistory(Base):
    """问答历史表 / QA history table"""
    __tablename__ = "qa_history"
    id = Column(String(36), primary_key=True)  # VARCHAR to match existing table
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    contexts = Column(JSONB, default=list)
    sources = Column(JSONB, default=dict)
    retrieval_method = Column(String(50))
    confidence = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation_id = Column(String(36))
```

---

### `backend/src/services/database_service.py`

**功能 / Purpose:**
统一的数据库连接和会话管理服务。

**核心类 / Core Classes:**
```python
class DatabaseService:
    """统一数据库服务 / Unified database service"""

    def __init__(self):
        # 使用 asyncpg 驱动
        connection_string = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self._engine = create_async_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def connect(self):
        """连接数据库 / Connect to database"""

    async def disconnect(self):
        """断开连接 / Disconnect"""

    async def create_tables(self):
        """创建所有表 / Create all tables"""

    @property
    def session_factory(self):
        """获取会话工厂 / Get session factory"""
```

---

### 修改的文件 / Modified Files

### `backend/pyproject.toml`

**新增依赖 / Added Dependencies:**
```toml
# Database ORM
"sqlalchemy[asyncio]>=2.0.0",  # SQLAlchemy async ORM
```

---

### `backend/src/services/auth_service.py`

**主要变更 / Major Changes:**
- 所有方法改为异步（`async`）
- 使用 SQLAlchemy ORM 替代 JSON 文件存储
- 添加 `await db_service.session_factory()` 上下文管理器

**变更示例 / Change Example:**
```python
# 之前 / Before: JSON 文件存储
def _load_users(self) -> List[User]:
    with open(self.users_file, "r") as f:
        data = json.load(f)
    return [User(**u) for u in data]

# 之后 / After: SQLAlchemy ORM
async def authenticate_user(self, username: str, password: str) -> Optional[User]:
    async with db_service.session_factory() as session:
        result = await session.execute(
            select(AppUser).where(AppUser.username == username)
        )
        db_user = result.scalar_one_or_none()
        # ... 验证逻辑
```

---

### `backend/src/services/audit_service.py`

**主要变更 / Major Changes:**
- 所有方法改为异步（`async`）
- 使用 SQLAlchemy ORM 存储审计日志
- JSONB 类型用于灵活的 details 存储

**变更示例 / Change Example:**
```python
async def log_action(self, action: AuditAction, ...):
    async with db_service.session_factory() as session:
        db_log = AuditLog(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            action=action.value,
            details=details,  # JSONB automatically
            # ...
        )
        session.add(db_log)
        await session.commit()
```

---

### `backend/src/services/document_registry.py`

**主要变更 / Major Changes:**
- 从原始 SQL 改为 SQLAlchemy ORM
- 字段名 `upload_date` → `created_at`（与数据库表结构匹配）

---

### `backend/src/services/qa_history_service.py`

**主要变更 / Major Changes:**
- 从原始 SQL 改为 SQLAlchemy ORM
- ID 类型使用 String(36) 而非 UUID（与现有表匹配）

---

### `backend/src/main.py`

**主要变更 / Major Changes:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时 / On startup
    await db_service.connect()
    await db_service.create_tables()  # 自动创建表
    await auth_service._create_default_admin()  # 创建默认管理员

    yield

    # 关闭时 / On shutdown
    await db_service.disconnect()
```

---

### 路由文件更新 / Router Files Update

**修改的文件 / Modified Files:**
- `backend/src/routers/auth.py`
- `backend/src/routers/audit.py`
- `backend/src/routers/permissions.py`

**变更内容 / Changes:**
- 所有服务调用添加 `await` 关键字
- 例如：`auth_service.authenticate_user()` → `await auth_service.authenticate_user()`

---

### 数据库表结构 / Database Table Structure

**创建表的 SQL 参考 / SQL Reference for Table Creation:**

```sql
-- 用户表 / User table
CREATE TABLE app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);

-- 审计日志表 / Audit log table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    action VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,
    username VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT
);

-- 文档注册表 / Document registry
CREATE TABLE document_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) UNIQUE NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    chunk_count INTEGER NOT NULL DEFAULT 0
);

-- 问答历史表 / QA history table
CREATE TABLE qa_history (
    id VARCHAR(36) PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    contexts JSONB NOT NULL DEFAULT '[]',
    sources JSONB NOT NULL DEFAULT '{}',
    retrieval_method VARCHAR(50),
    confidence INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    conversation_id VARCHAR(36)
);
```

**索引 / Indexes:**
```sql
CREATE INDEX idx_app_users_username ON app_users(username);
CREATE INDEX idx_app_users_email ON app_users(email);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_document_registry_filename ON document_registry(filename);
CREATE INDEX idx_qa_history_created_at ON qa_history(created_at);
```

---

### 兼容性说明 / Compatibility Notes

1. **现有数据 / Existing Data:** 本次迁移与现有数据库表结构兼容，不会影响 rag_documents 表（由 LangChain PGVector 管理）

2. **类型匹配 / Type Matching:**
   - `qa_history.id` 和 `conversation_id` 使用 VARCHAR(36) 以匹配现有表结构
   - 其他表使用 UUID 类型

3. **字段名称 / Field Names:**
   - `document_registry.created_at` 而非 `upload_date`

---

### 迁移后验证 / Post-Migration Verification

启动后端服务时，会自动：
1. 连接到数据库
2. 创建所有表（如果不存在）
3. 创建默认管理员用户（admin / admin123）

---

## 7. Bug 修复 / Bug Fix (2026-04-12)

### 文档删除失败修复

**问题 / Issue:** `vector_store.delete_document()` 使用 `filter={"filename": document_id}` 删除文档，但 `document_id` 是 UUID，`filename` 存储的是原始文件名，导致过滤器永远匹配不到任何文档，删除操作静默失败。

**修复 / Fix:**
- `store_document()`: 在创建文档前生成 `doc_id = str(uuid.uuid4())`，将 `doc_id` 写入每个 chunk 的 metadata，返回 `doc_id` 而非 PGVector 的 `ids[0]`
- `delete_document()`: 过滤条件改为 `filter={"doc_id": document_id}`

**修改文件 / Modified Files:**
- `backend/src/services/vector_store.py` (添加 `import uuid`；修改 `store_document` 和 `delete_document`)

### 健康检查端点修复

**问题 / Issue:** `health_check` 端点 `status` 硬编码为 "healthy"；只检查 `vector_store` 不检查 `db_service`；访问私有属性 `_vectorstore`；无实际连接活性测试。

**修复 / Fix:**
- `database_service.py`: 添加 `health_check()` 方法执行 `SELECT 1` 验证连接活性
- `vector_store.py`: 添加公开的 `health_check()` 方法
- `main.py`: 重写端点，分别检查两个服务，不健康时返回 HTTP 503；`audit_service.get_logs` 包裹在 try/except 中
- `schemas.py`: HealthResponse 字段从 `database: str` 拆分为 `db_status: str` + `vector_status: str`

**修改文件 / Modified Files:**
- `backend/src/services/database_service.py` (添加 `health_check` 方法)
- `backend/src/services/vector_store.py` (添加 `health_check` 方法)
- `backend/src/main.py` (重写健康检查端点，安全化审计日志查询)
- `backend/src/models/schemas.py` (HealthResponse 字段拆分)

---

## 8. 后续改进 / Future Improvements (Day 7+)

- [x] 用户数据持久化到 PostgreSQL ✅ (已完成)
- [x] 审计日志持久化到 PostgreSQL ✅ (已完成)
- [ ] OAuth2/OIDC 集成
- [ ] 双因素认证（2FA）
- [ ] 更复杂的内容过滤规则
- [ ] 审计日志导出到外部系统
- [ ] 实时安全告警
- [ ] Docker 部署配置
