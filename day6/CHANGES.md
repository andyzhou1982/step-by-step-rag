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

## 6. 后续改进 / Future Improvements (Day 7+)

- [ ] 用户数据持久化到 PostgreSQL
- [ ] 权限数据持久化到 PostgreSQL
- [ ] OAuth2/OIDC 集成
- [ ] 双因素认证（2FA）
- [ ] 更复杂的内容过滤规则
- [ ] 审计日志导出到外部系统
- [ ] 实时安全告警
- [ ] Docker 部署配置
