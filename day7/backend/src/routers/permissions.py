"""
Permission management API routes
权限管理 API 路由

Day 6: Security & Governance
Day 6： 安全与治理
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List

from models.schemas import (
    PermissionGrantRequest,
    PermissionInfo,
    DocumentPermissionsResponse,
    ApiResponse,
)
from services.auth_service import auth_service, User
from services.auth_service import auth_service
from services.permission_service import permission_service, Permission
from services.audit_service import audit_service, AuditAction
from routers.auth import get_current_user, require_role, get_client_ip


router = APIRouter(prefix="/permissions", tags=["Permissions (Day 6)"])


@router.post("/grant", response_model=PermissionInfo)
async def grant_permission(
    request: Request,
    req: PermissionGrantRequest,
    current_user: User = Depends(require_role("admin"))
):
    """
    Grant a permission to a user for a document (admin only)
    授予用户对文档的权限（仅管理员）

    Day 6: New endpoint for permission grant
    Day 6： 权限授予的新端点
    """
    # Validate permission type
    # 验证权限类型
    try:
        permission = Permission(req.permission)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission. Must be one of: read, write, admin"
        )

    # Check if target user exists
    # 检查目标用户是否存在
    target_user = auth_service.get_user_by_id(req.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Grant permission
    # 授予权限
    perm = permission_service.grant_permission(
        document_id=req.document_id,
        user_id=req.user_id,
        permission=permission,
        granted_by=current_user.id,
    )

    # Log action
    # 记录操作
    audit_service.log_action(
        action=AuditAction.PERMISSION_GRANT,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="document",
        resource_id=req.document_id,
        details={
            "granted_to": req.user_id,
            "permission": req.permission,
        },
        ip_address=get_client_ip(request),
    )

    return PermissionInfo(
        document_id=perm.document_id,
        user_id=perm.user_id,
        permission=perm.permission.value,
        granted_by=perm.granted_by,
        granted_at=perm.granted_at,
    )


@router.delete("/revoke/{document_id}/{user_id}")
async def revoke_permission(
    document_id: str,
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    """
    Revoke a permission from a user for a document (admin only)
    撤销用户对文档的权限（仅管理员）

    Day 6: New endpoint for permission revocation
    Day 6： 权限撤销的新端点
    """
    revoked = permission_service.revoke_permission(document_id, user_id)

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="Permission not found"
        )

    # Log action
    # 记录操作
    audit_service.log_action(
        action=AuditAction.PERMISSION_REVOKE,
        user_id=current_user.id,
        username=current_user.username,
        resource_type="document",
        resource_id=document_id,
        details={
            "revoked_from": user_id,
        },
        ip_address=get_client_ip(request),
    )

    return {"message": "Permission revoked successfully"}


@router.get("/document/{document_id}", response_model=DocumentPermissionsResponse)
async def get_document_permissions(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions for a document
    获取文档的所有权限

    Day 6: New endpoint for document permissions
    Day 6： 文档权限的新端点
    """
    permissions = permission_service.get_document_permissions(document_id)

    return DocumentPermissionsResponse(
        document_id=document_id,
        permissions=[
            PermissionInfo(
                document_id=p.document_id,
                user_id=p.user_id,
                permission=p.permission.value,
                granted_by=p.granted_by,
                granted_at=p.granted_at,
            )
            for p in permissions
        ],
    )


@router.get("/user/{user_id}", response_model=List[PermissionInfo])
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all permissions for a user
    获取用户的所有权限

    Day 6: New endpoint for user permissions
    Day 6： 用户权限的新端点
    """
    # Users can only view their own permissions unless admin
    # 除非是管理员，否则用户只能查看自己的权限
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot view other users' permissions"
        )

    permissions = permission_service.get_user_permissions(user_id)

    return [
        PermissionInfo(
            document_id=p.document_id,
            user_id=p.user_id,
            permission=p.permission.value,
            granted_by=p.granted_by,
            granted_at=p.granted_at,
        )
        for p in permissions
    ]


@router.get("/check/{document_id}")
async def check_permission(
    document_id: str,
    required_permission: str = "read",
    current_user: User = Depends(get_current_user)
):
    """
    Check if current user has a specific permission for a document
    检查当前用户对文档是否有特定权限

    Day 6: New endpoint for permission check
    Day 6： 权限检查的新端点
    """
    # Validate permission type
    # 验证权限类型
    try:
        permission = Permission(required_permission)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permission. Must be one of: read, write, admin"
        )

    has_permission = permission_service.check_permission(
        document_id=document_id,
        user_id=current_user.id,
        required_permission=permission,
        user_role=current_user.role,
    )

    return {
        "document_id": document_id,
        "user_id": current_user.id,
        "required_permission": required_permission,
        "has_permission": has_permission,
    }
