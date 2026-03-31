"""
Audit logging service for tracking user actions
追踪用户操作的审计日志服务

Day 6: Security & Governance
Day 6： 安全与治理
"""

import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from config import settings, get_logger

logger = get_logger(__name__)


class AuditAction(Enum):
    """
    Types of audit actions
    审计操作类型

    Day 6: New enum for audit action types
    Day 6： 审计操作类型的新枚举
    """
    # Authentication actions / 认证操作
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"

    # User management actions / 用户管理操作
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DEACTIVATE = "user_deactivate"
    USER_ACTIVATE = "user_activate"

    # Document actions / 文档操作
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"

    # Chat actions / 聊天操作
    CHAT_QUERY = "chat_query"
    CHAT_STREAM = "chat_stream"

    # Permission actions / 权限操作
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"

    # System actions / 系统操作
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SYSTEM_ERROR = "system_error"


@dataclass
class AuditLog:
    """
    Audit log entry
    审计日志条目

    Day 6: New model for audit log
    Day 6： 审计日志的新模型
    """
    id: str
    timestamp: datetime
    action: AuditAction
    user_id: str
    username: str
    resource_type: str  # "document", "user", "chat", "system"
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"  # "success", "failed", "error"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary
        转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "user_id": self.user_id,
            "username": self.username,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
        }


class AuditService:
    """
    Service for recording and querying audit logs
    记录和查询审计日志的服务

    Day 6: New service for audit logging
    Day 6： 审计日志的新服务

    Features:
    - Record user actions
    - Query audit logs by various filters
    - Automatic log retention management
    - Export audit logs
    """

    def __init__(self):
        # In-memory log storage (for demo)
        # 内存日志存储（用于演示）
        # In production, use database or log aggregation system
        # 生产环境中，使用数据库或日志聚合系统
        self._logs: List[AuditLog] = []
        self._logs_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "audit_logs.json")
        self._load_logs()

    def _load_logs(self):
        """Load logs from file
        从文件加载日志"""
        try:
            if os.path.exists(self._logs_file):
                with open(self._logs_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for log_data in data.get("logs", []):
                        log = AuditLog(
                            id=log_data["id"],
                            timestamp=datetime.fromisoformat(log_data["timestamp"]),
                            action=AuditAction(log_data["action"]),
                            user_id=log_data["user_id"],
                            username=log_data["username"],
                            resource_type=log_data["resource_type"],
                            resource_id=log_data.get("resource_id"),
                            details=log_data.get("details", {}),
                            ip_address=log_data.get("ip_address"),
                            user_agent=log_data.get("user_agent"),
                            status=log_data.get("status", "success"),
                            error_message=log_data.get("error_message"),
                        )
                        self._logs.append(log)
        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            self._logs = []

    def _save_logs(self):
        """Save logs to file
        保存日志到文件"""
        try:
            os.makedirs(os.path.dirname(self._logs_file), exist_ok=True)

            # Clean up old logs based on retention policy
            # 根据保留策略清理旧日志
            cutoff_date = datetime.now() - timedelta(days=settings.audit_log_retention_days)
            self._logs = [log for log in self._logs if log.timestamp >= cutoff_date]

            data = {
                "logs": [log.to_dict() for log in self._logs],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self._logs_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving audit logs: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")

    def log_action(
        self,
        action: AuditAction,
        user_id: str,
        username: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Record an audit log entry
        记录审计日志条目

        Args:
            action: Type of action performed
                   执行的操作类型
            user_id: ID of user who performed the action
                    执行操作的用户 ID
            username: Username of user who performed the action
                     执行操作的用户名
            resource_type: Type of resource affected
                          受影响的资源类型
            resource_id: ID of resource affected (optional)
                        受影响的资源 ID（可选）
            details: Additional details about the action
                    操作的额外详情
            ip_address: IP address of the request
                       请求的 IP 地址
            user_agent: User agent string
                       用户代理字符串
            status: Status of the action (success/failed/error)
                   操作状态（success/failed/error）
            error_message: Error message if status is failed/error
                          如果状态是 failed/error 的错误消息
        Returns:
            Created AuditLog entry
            创建的 AuditLog 条目
        """
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )

        self._logs.append(log)
        self._save_logs()

        return log

    def log_login(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """
        Convenience method to log login attempts
        记录登录尝试的便捷方法

        Args:
            user_id: User ID
                    用户 ID
            username: Username
                     用户名
            ip_address: IP address
                       IP 地址
            user_agent: User agent
                       用户代理
            success: Whether login was successful
                    登录是否成功
        Returns:
            Created AuditLog entry
            创建的 AuditLog 条目
        """
        return self.log_action(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            user_id=user_id,
            username=username,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failed",
            error_message=None if success else "Invalid credentials",
        )

    def log_logout(
        self,
        user_id: str,
        username: str,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Convenience method to log logout
        记录登出的便捷方法

        Args:
            user_id: User ID
                    用户 ID
            username: Username
                     用户名
            ip_address: IP address
                       IP 地址
        Returns:
            Created AuditLog entry
            创建的 AuditLog 条目
        """
        return self.log_action(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            username=username,
            resource_type="user",
            resource_id=user_id,
            ip_address=ip_address,
        )

    def log_document_action(
        self,
        action: AuditAction,
        user_id: str,
        username: str,
        document_id: str,
        filename: str,
        ip_address: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Convenience method to log document actions
        记录文档操作的便捷方法

        Args:
            action: Document action type
                   文档操作类型
            user_id: User ID
                    用户 ID
            username: Username
                     用户名
            document_id: Document ID
                        文档 ID
            filename: Document filename
                     文档文件名
            ip_address: IP address
                       IP 地址
            status: Status of the action
                   操作状态
            error_message: Error message if failed
                          如果失败的错误消息
        Returns:
            Created AuditLog entry
            创建的 AuditLog 条目
        """
        return self.log_action(
            action=action,
            user_id=user_id,
            username=username,
            resource_type="document",
            resource_id=document_id,
            details={"filename": filename},
            ip_address=ip_address,
            status=status,
            error_message=error_message,
        )

    def log_chat_action(
        self,
        action: AuditAction,
        user_id: str,
        username: str,
        conversation_id: str,
        query_preview: str,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Convenience method to log chat actions
        记录聊天操作的便捷方法

        Args:
            action: Chat action type
                   聊天操作类型
            user_id: User ID
                    用户 ID
            username: Username
                     用户名
            conversation_id: Conversation ID
                            对话 ID
            query_preview: Preview of the query (first 100 chars)
                          查询预览（前 100 个字符）
            ip_address: IP address
                       IP 地址
        Returns:
            Created AuditLog entry
            创建的 AuditLog 条目
        """
        return self.log_action(
            action=action,
            user_id=user_id,
            username=username,
            resource_type="chat",
            resource_id=conversation_id,
            details={"query_preview": query_preview[:100]},
            ip_address=ip_address,
        )

    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filters
        使用过滤器查询审计日志

        Args:
            user_id: Filter by user ID
                    按用户 ID 过滤
            action: Filter by action type
                   按操作类型过滤
            resource_type: Filter by resource type
                          按资源类型过滤
            resource_id: Filter by resource ID
                        按资源 ID 过滤
            start_date: Filter by start date
                       按开始日期过滤
            end_date: Filter by end date
                     按结束日期过滤
            status: Filter by status
                   按状态过滤
            limit: Maximum number of results
                  最大结果数
            offset: Offset for pagination
                   分页偏移量
        Returns:
            List of matching AuditLog entries
            匹配的 AuditLog 条目列表
        """
        filtered = self._logs

        # Apply filters
        # 应用过滤器
        if user_id:
            filtered = [log for log in filtered if log.user_id == user_id]
        if action:
            filtered = [log for log in filtered if log.action == action]
        if resource_type:
            filtered = [log for log in filtered if log.resource_type == resource_type]
        if resource_id:
            filtered = [log for log in filtered if log.resource_id == resource_id]
        if start_date:
            filtered = [log for log in filtered if log.timestamp >= start_date]
        if end_date:
            filtered = [log for log in filtered if log.timestamp <= end_date]
        if status:
            filtered = [log for log in filtered if log.status == status]

        # Sort by timestamp (newest first)
        # 按时间戳排序（最新的在前）
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        # 应用分页
        return filtered[offset:offset + limit]

    def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get activity summary for a user
        获取用户的活动摘要

        Args:
            user_id: User ID
                    用户 ID
            days: Number of days to include
                 包含的天数
        Returns:
            Activity summary dictionary
            活动摘要字典
        """
        start_date = datetime.now() - timedelta(days=days)
        user_logs = self.get_logs(user_id=user_id, start_date=start_date)

        # Count actions by type
        # 按类型统计操作
        action_counts: Dict[str, int] = {}
        for log in user_logs:
            action_name = log.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(user_logs),
            "action_counts": action_counts,
            "last_activity": user_logs[0].timestamp.isoformat() if user_logs else None,
        }

    def get_system_activity_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get system-wide activity summary
        获取系统范围的活动摘要

        Args:
            days: Number of days to include
                 包含的天数
        Returns:
            System activity summary dictionary
            系统活动摘要字典
        """
        start_date = datetime.now() - timedelta(days=days)
        all_logs = self.get_logs(start_date=start_date, limit=10000)

        # Count actions by type
        # 按类型统计操作
        action_counts: Dict[str, int] = {}
        user_counts: Dict[str, int] = {}
        resource_counts: Dict[str, int] = {}

        for log in all_logs:
            # Count by action
            # 按操作统计
            action_name = log.action.value
            action_counts[action_name] = action_counts.get(action_name, 0) + 1

            # Count by user
            # 按用户统计
            user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1

            # Count by resource type
            # 按资源类型统计
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1

        return {
            "period_days": days,
            "total_actions": len(all_logs),
            "unique_users": len(user_counts),
            "action_counts": action_counts,
            "resource_counts": resource_counts,
        }

    def export_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs to file format
        将审计日志导出为文件格式

        Args:
            format: Export format (json, csv)
                   导出格式（json, csv）
            start_date: Start date filter
                       开始日期过滤
            end_date: End date filter
                     结束日期过滤
        Returns:
            Exported data as string
            导出的数据字符串
        """
        logs = self.get_logs(start_date=start_date, end_date=end_date, limit=10000)

        if format == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2)
        elif format == "csv":
            # Simple CSV export
            # 简单的 CSV 导出
            lines = ["id,timestamp,action,user_id,username,resource_type,resource_id,status"]
            for log in logs:
                lines.append(
                    f"{log.id},{log.timestamp.isoformat()},{log.action.value},"
                    f"{log.user_id},{log.username},{log.resource_type},"
                    f"{log.resource_id or ''},{log.status}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global audit service instance
# 全局审计服务实例
audit_service = AuditService()
