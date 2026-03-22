"""
Authentication and user management API routes
认证和用户管理 API 路由

Day 6: Security & Governance
Day 6： 安全与治理
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Optional
from datetime import datetime, timedelta

from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserInfo,
    UserListResponse,
    UserRoleUpdateRequest,
    ApiResponse,
)
from services.auth_service import auth_service, User
from services.audit_service import audit_service, AuditAction
from services.content_filter_service import content_filter_service
from config import settings


router = APIRouter(prefix="/auth", tags=["Authentication (Day 6)"])


# ==================== Helper Functions ====================
# ==================== 辅助函数 ====================

def get_client_ip(request: Request) -> Optional[str]:
    """Get client IP address from request
    从请求获取客户端 IP 地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Dependency to get current user from JWT token
    从 JWT token 获取当前用户的依赖

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not settings.auth_enabled:
        # If auth is disabled, return a default user
        # 如果认证被禁用，返回默认用户
        return User(
            id="anonymous",
            username="anonymous",
            email="anonymous@example.com",
            hashed_password="",
            role="admin",
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    # 从 "Bearer <token>" 提取 token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    token_data = auth_service.decode_token(token)

    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    Dependency to optionally get current user (doesn't raise if no token)
    可选地获取当前用户的依赖（如果没有 token 不会抛出异常）
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency factory to require a specific role
    要求特定角色的依赖工厂

    Args:
        required_role: Required role ("admin", "user", "viewer")
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {"admin": 3, "user": 2, "viewer": 1}
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    return role_checker


# ==================== Authentication Endpoints ====================
# ==================== 认证端点 ====================

@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    req: UserRegisterRequest
):
    """
    Register a new user
    注册新用户

    Day 6: New endpoint for user registration
    Day 6： 用户注册的新端点
    """
    try:
        # Filter input for security
        # 过滤输入以确保安全
        if settings.content_filter_enabled:
            filter_result = content_filter_service.filter_input(
                req.username,
                check_sql_injection=True,
                check_xss=True,
                check_prompt_injection=False,
            )
            if not filter_result.is_safe:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid username: {', '.join(filter_result.blocked_reasons)}"
                )

        # Register user
        # 注册用户
        user = auth_service.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
            role=req.role,
        )

        # Generate token
        # 生成 token
        token = auth_service.create_access_token(user)

        # Log registration
        # 记录注册
        audit_service.log_action(
            action=AuditAction.USER_CREATE,
            user_id=user.id,
            username=user.username,
            resource_type="user",
            resource_id=user.id,
            ip_address=get_client_ip(request),
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_hours * 3600,
            user_id=user.id,
            username=user.username,
            role=user.role,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    req: UserLoginRequest
):
    """
    Login and get JWT token
    登录并获取 JWT token

    Day 6: New endpoint for user login
    Day 6： 用户登录的新端点
    """
    # Authenticate user
    # 认证用户
    user = auth_service.authenticate_user(req.username, req.password)

    if not user:
        # Log failed login attempt
        # 记录失败的登录尝试
        audit_service.log_login(
            user_id="unknown",
            username=req.username,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            success=False,
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Generate token
    # 生成 token
    token = auth_service.create_access_token(user)

    # Log successful login
    # 记录成功的登录
    audit_service.log_login(
        user_id=user.id,
        username=user.username,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        success=True,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_hours * 3600,
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user
    登出当前用户

    Day 6: New endpoint for user logout
    Day 6： 用户登出的新端点
    """
    # Log logout
    # 记录登出
    audit_service.log_logout(
        user_id=current_user.id,
        username=current_user.username,
        ip_address=get_client_ip(request),
    )

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    获取当前用户信息

    Day 6: New endpoint for user info
    Day 6： 用户信息的新端点
    """
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


# ==================== User Management Endpoints ====================
# ==================== 用户管理端点 ====================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(require_role("admin"))
):
    """
    List all users (admin only)
    列出所有用户（仅管理员）

    Day 6: New endpoint for user list
    Day 6： 用户列表的新端点
    """
    users = auth_service.get_all_users()
    return UserListResponse(
        users=[
            UserInfo(
                id=u.id,
                username=u.username,
                email=u.email,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                last_login=u.last_login,
            )
            for u in users
        ],
        total=len(users),
    )


@router.put("/users/{user_id}/role", response_model=UserInfo)
async def update_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    """
    Update a user's role (admin only)
    更新用户角色（仅管理员）

    Day 6: New endpoint for role update
    Day 6： 角色更新的新端点
    """
    # Validate role
    # 验证角色
    valid_roles = ["admin", "user", "viewer"]
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )

    # Update role
    # 更新角色
    user = auth_service.update_user_role(user_id, req.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log action
    # 记录操作
    audit_service.log_action(
        action=AuditAction.USER_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user_id,
        details={"new_role": req.role},
        ip_address=get_client_ip(request),
    )

    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/users/{user_id}/deactivate", response_model=UserInfo)
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    """
    Deactivate a user (admin only)
    停用用户（仅管理员）

    Day 6: New endpoint for user deactivation
    Day 6： 停用用户的新端点
    """
    # Prevent self-deactivation
    # 防止自我停用
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate yourself"
        )

    user = auth_service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log action
    # 记录操作
    audit_service.log_action(
        action=AuditAction.USER_DEACTIVATE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user_id,
        ip_address=get_client_ip(request),
    )

    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/users/{user_id}/activate", response_model=UserInfo)
async def activate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    """
    Activate a user (admin only)
    激活用户（仅管理员）

    Day 6: New endpoint for user activation
    Day 6： 激活用户的新端点
    """
    user = auth_service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log action
    # 记录操作
    audit_service.log_action(
        action=AuditAction.USER_ACTIVATE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user_id,
        ip_address=get_client_ip(request),
    )

    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )
