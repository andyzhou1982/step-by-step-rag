"""
Audit log API routes
审计日志 API 路由

Day 6: Security & Governance
Day 6： 安全与治理
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime
from typing import Optional

from models.schemas import (
    AuditLogEntry,
    AuditLogListResponse,
    AuditSummaryResponse,
)
from services.auth_service import User
from services.audit_service import audit_service, AuditAction
from routers.auth import get_current_user, require_role, get_client_ip


router = APIRouter(prefix="/audit", tags=["Audit (Day 6)"])


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(require_role("admin"))
):
    """
    Get audit logs with filters (admin only)
    使用过滤器获取审计日志（仅管理员）

    Day 6: New endpoint for audit log query
    Day 6： 审计日志查询的新端点
    """
    # Parse action if provided
    # 如果提供了 action 则解析
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action type: {action}"
            )

    logs = audit_service.get_logs(
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        limit=limit,
        offset=offset,
    )

    # Get total count (approximate - using same filters)
    # 获取总数（近似 - 使用相同的过滤器）
    total_logs = audit_service.get_logs(
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        limit=10000,  # Get all to count
        offset=0,
    )

    return AuditLogListResponse(
        logs=[
            AuditLogEntry(
                id=log.id,
                timestamp=log.timestamp,
                action=log.action.value,
                user_id=log.user_id,
                username=log.username,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                status=log.status,
            )
            for log in logs
        ],
        total=len(total_logs),
        limit=limit,
        offset=offset,
    )


@router.get("/user/{user_id}/activity", response_model=dict)
async def get_user_activity(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to include"),
    current_user: User = Depends(require_role("admin"))
):
    """
    Get activity summary for a specific user (admin only)
    获取特定用户的活动摘要（仅管理员）

    Day 6: New endpoint for user activity
    Day 6： 用户活动的新端点
    """
    summary = audit_service.get_user_activity_summary(user_id, days)
    return summary


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_system_activity_summary(
    days: int = Query(7, ge=1, le=30, description="Number of days to include"),
    current_user: User = Depends(require_role("admin"))
):
    """
    Get system-wide activity summary (admin only)
    获取系统范围的活动摘要（仅管理员）

    Day 6: New endpoint for system activity summary
    Day 6： 系统活动摘要的新端点
    """
    summary = audit_service.get_system_activity_summary(days)

    return AuditSummaryResponse(
        period_days=summary["period_days"],
        total_actions=summary["total_actions"],
        unique_users=summary["unique_users"],
        action_counts=summary["action_counts"],
        resource_counts=summary["resource_counts"],
    )


@router.get("/my-activity")
async def get_my_activity(
    days: int = Query(7, ge=1, le=30, description="Number of days to include"),
    current_user: User = Depends(get_current_user)
):
    """
    Get activity summary for the current user
    获取当前用户的活动摘要

    Day 6: New endpoint for user's own activity
    Day 6： 用户自身活动的新端点
    """
    summary = audit_service.get_user_activity_summary(current_user.id, days)
    return summary


@router.get("/export")
async def export_audit_logs(
    format: str = Query("json", description="Export format (json or csv)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(require_role("admin"))
):
    """
    Export audit logs to file format (admin only)
    将审计日志导出为文件格式（仅管理员）

    Day 6: New endpoint for audit log export
    Day 6： 审计日志导出的新端点
    """
    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Must be 'json' or 'csv'"
        )

    exported_data = audit_service.export_logs(
        format=format,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "format": format,
        "data": exported_data,
        "message": "Audit logs exported successfully",
    }


@router.get("/actions")
async def get_available_actions(
    current_user: User = Depends(require_role("admin"))
):
    """
    Get list of available audit action types
    获取可用的审计操作类型列表

    Day 6: New endpoint for action types
    Day 6： 操作类型的新端点
    """
    actions = [
        {"value": action.value, "description": _get_action_description(action)}
        for action in AuditAction
    ]
    return {"actions": actions}


def _get_action_description(action: AuditAction) -> str:
    """Get human-readable description for an action
    获取操作的可读描述"""
    descriptions = {
        AuditAction.LOGIN: "User logged in / 用户登录",
        AuditAction.LOGOUT: "User logged out / 用户登出",
        AuditAction.LOGIN_FAILED: "Failed login attempt / 登录尝试失败",
        AuditAction.USER_CREATE: "User account created / 用户账户创建",
        AuditAction.USER_UPDATE: "User account updated / 用户账户更新",
        AuditAction.USER_DEACTIVATE: "User account deactivated / 用户账户停用",
        AuditAction.USER_ACTIVATE: "User account activated / 用户账户激活",
        AuditAction.DOCUMENT_UPLOAD: "Document uploaded / 文档上传",
        AuditAction.DOCUMENT_DELETE: "Document deleted / 文档删除",
        AuditAction.DOCUMENT_VIEW: "Document viewed / 文档查看",
        AuditAction.DOCUMENT_DOWNLOAD: "Document downloaded / 文档下载",
        AuditAction.CHAT_QUERY: "Chat query submitted / 聊天查询提交",
        AuditAction.CHAT_STREAM: "Chat stream started / 聊天流开始",
        AuditAction.PERMISSION_GRANT: "Permission granted / 权限授予",
        AuditAction.PERMISSION_REVOKE: "Permission revoked / 权限撤销",
        AuditAction.SYSTEM_CONFIG_CHANGE: "System configuration changed / 系统配置更改",
        AuditAction.SYSTEM_ERROR: "System error occurred / 系统错误发生",
    }
    return descriptions.get(action, action.value)
