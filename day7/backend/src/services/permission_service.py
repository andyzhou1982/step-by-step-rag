"""
Permission and Access Control List (ACL) service
权限和访问控制列表（ACL）服务

Day 6: Security & Governance
Day 6： 安全与治理
"""

import os
import json
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from config import get_logger

logger = get_logger(__name__)


class Permission(Enum):
    """
    Permission levels for documents
    文档的权限级别

    Day 6: New enum for permission types
    Day 6： 权限类型的新枚举
    """
    READ = "read"        # Can view document / 可以查看文档
    WRITE = "write"      # Can edit document / 可以编辑文档
    ADMIN = "admin"      # Can delete and manage permissions / 可以删除和管理权限


@dataclass
class DocumentPermission:
    """
    Permission entry for a document
    文档的权限条目

    Day 6: New model for document permission
    Day 6： 文档权限的新模型
    """
    document_id: str
    user_id: str
    permission: Permission
    granted_by: str  # User ID who granted the permission
    granted_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary
        转换为字典"""
        return {
            "document_id": self.document_id,
            "user_id": self.user_id,
            "permission": self.permission.value,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
        }


@dataclass
class RolePermission:
    """
    Default permissions for a role
    角色的默认权限

    Day 6: New model for role-based permissions
    Day 6： 基于角色权限的新模型
    """
    role: str
    default_permission: Permission
    can_grant_permissions: bool = False
    can_manage_users: bool = False


class PermissionService:
    """
    Service for managing document-level permissions
    管理文档级权限的服务

    Day 6: New service for ACL management
    Day 6： ACL 管理的新服务

    Features:
    - Document-level permission control
    - Role-based default permissions
    - Permission inheritance
    - Permission checking and validation
    """

    def __init__(self):
        # In-memory permission storage
        # 内存权限存储
        # Key: document_id, Value: Dict[user_id, DocumentPermission]
        self._permissions: Dict[str, Dict[str, DocumentPermission]] = {}
        self._permissions_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "permissions.json")
        self._load_permissions()

        # Role-based default permissions
        # 基于角色的默认权限
        self._role_permissions: Dict[str, RolePermission] = {
            "admin": RolePermission(
                role="admin",
                default_permission=Permission.ADMIN,
                can_grant_permissions=True,
                can_manage_users=True,
            ),
            "user": RolePermission(
                role="user",
                default_permission=Permission.WRITE,
                can_grant_permissions=False,
                can_manage_users=False,
            ),
            "viewer": RolePermission(
                role="viewer",
                default_permission=Permission.READ,
                can_grant_permissions=False,
                can_manage_users=False,
            ),
        }

    def _load_permissions(self):
        """Load permissions from file
        从文件加载权限"""
        try:
            if os.path.exists(self._permissions_file):
                with open(self._permissions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for perm_data in data.get("permissions", []):
                        perm = DocumentPermission(
                            document_id=perm_data["document_id"],
                            user_id=perm_data["user_id"],
                            permission=Permission(perm_data["permission"]),
                            granted_by=perm_data["granted_by"],
                            granted_at=datetime.fromisoformat(perm_data["granted_at"]),
                        )
                        if perm.document_id not in self._permissions:
                            self._permissions[perm.document_id] = {}
                        self._permissions[perm.document_id][perm.user_id] = perm
        except Exception as e:
            logger.error(f"Error loading permissions: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            self._permissions = {}

    def _save_permissions(self):
        """Save permissions to file
        保存权限到文件"""
        try:
            os.makedirs(os.path.dirname(self._permissions_file), exist_ok=True)

            data = {
                "permissions": [
                    perm.to_dict()
                    for doc_perms in self._permissions.values()
                    for perm in doc_perms.values()
                ]
            }

            with open(self._permissions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving permissions: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")

    def grant_permission(
        self,
        document_id: str,
        user_id: str,
        permission: Permission,
        granted_by: str
    ) -> DocumentPermission:
        """
        Grant a permission to a user for a document
        授予用户对文档的权限

        Args:
            document_id: Document ID
                        文档 ID
            user_id: User ID to grant permission to
                    要授予权限的用户 ID
            permission: Permission level to grant
                       要授予的权限级别
            granted_by: User ID of the user granting the permission
                       授予权限的用户 ID
        Returns:
            Created DocumentPermission
            创建的 DocumentPermission
        """
        if document_id not in self._permissions:
            self._permissions[document_id] = {}

        perm = DocumentPermission(
            document_id=document_id,
            user_id=user_id,
            permission=permission,
            granted_by=granted_by,
        )

        self._permissions[document_id][user_id] = perm
        self._save_permissions()

        return perm

    def revoke_permission(self, document_id: str, user_id: str) -> bool:
        """
        Revoke a permission from a user for a document
        撤销用户对文档的权限

        Args:
            document_id: Document ID
                        文档 ID
            user_id: User ID to revoke permission from
                    要撤销权限的用户 ID
        Returns:
            True if permission was revoked
            如果权限被撤销则返回 True
        """
        if document_id in self._permissions:
            if user_id in self._permissions[document_id]:
                del self._permissions[document_id][user_id]
                self._save_permissions()
                return True
        return False

    def check_permission(
        self,
        document_id: str,
        user_id: str,
        required_permission: Permission,
        user_role: str = "user"
    ) -> bool:
        """
        Check if a user has a specific permission for a document
        检查用户对文档是否有特定权限

        Args:
            document_id: Document ID
                        文档 ID
            user_id: User ID to check
                    要检查的用户 ID
            required_permission: Required permission level
                                所需权限级别
            user_role: User's role for default permissions
                      用于默认权限的用户角色
        Returns:
            True if user has the permission
            如果用户有权限则返回 True
        """
        # Admin role has all permissions
        # 管理员角色拥有所有权限
        if user_role == "admin":
            return True

        # Check explicit permissions
        # 检查显式权限
        if document_id in self._permissions:
            if user_id in self._permissions[document_id]:
                user_perm = self._permissions[document_id][user_id].permission
                return self._permission_sufficient(user_perm, required_permission)

        # Check default role permissions
        # 检查默认角色权限
        if user_role in self._role_permissions:
            default_perm = self._role_permissions[user_role].default_permission
            return self._permission_sufficient(default_perm, required_permission)

        return False

    def _permission_sufficient(
        self,
        user_permission: Permission,
        required_permission: Permission
    ) -> bool:
        """
        Check if user permission level is sufficient for required permission
        检查用户权限级别是否满足所需权限

        Args:
            user_permission: User's permission level
                           用户的权限级别
            required_permission: Required permission level
                                所需权限级别
        Returns:
            True if sufficient
            如果足够则返回 True
        """
        # Permission hierarchy: ADMIN > WRITE > READ
        # 权限层次：ADMIN > WRITE > READ
        permission_levels = {
            Permission.READ: 1,
            Permission.WRITE: 2,
            Permission.ADMIN: 3,
        }

        user_level = permission_levels.get(user_permission, 0)
        required_level = permission_levels.get(required_permission, 0)

        return user_level >= required_level

    def get_document_permissions(self, document_id: str) -> List[DocumentPermission]:
        """
        Get all permissions for a document
        获取文档的所有权限

        Args:
            document_id: Document ID
                        文档 ID
        Returns:
            List of DocumentPermission objects
            DocumentPermission 对象列表
        """
        if document_id in self._permissions:
            return list(self._permissions[document_id].values())
        return []

    def get_user_permissions(self, user_id: str) -> List[DocumentPermission]:
        """
        Get all permissions for a user
        获取用户的所有权限

        Args:
            user_id: User ID
                    用户 ID
        Returns:
            List of DocumentPermission objects
            DocumentPermission 对象列表
        """
        permissions = []
        for doc_perms in self._permissions.values():
            if user_id in doc_perms:
                permissions.append(doc_perms[user_id])
        return permissions

    def can_grant_permissions(self, user_role: str) -> bool:
        """
        Check if a role can grant permissions to others
        检查角色是否可以授予他人权限

        Args:
            user_role: User's role
                      用户角色
        Returns:
            True if can grant permissions
            如果可以授予权限则返回 True
        """
        if user_role in self._role_permissions:
            return self._role_permissions[user_role].can_grant_permissions
        return False

    def remove_document_permissions(self, document_id: str):
        """
        Remove all permissions for a document (when document is deleted)
        删除文档的所有权限（当文档被删除时）

        Args:
            document_id: Document ID
                        文档 ID
        """
        if document_id in self._permissions:
            del self._permissions[document_id]
            self._save_permissions()

    def filter_documents_by_permission(
        self,
        document_ids: List[str],
        user_id: str,
        required_permission: Permission,
        user_role: str = "user"
    ) -> List[str]:
        """
        Filter document list to only include accessible documents
        过滤文档列表，只包含可访问的文档

        Args:
            document_ids: List of document IDs to filter
                         要过滤的文档 ID 列表
            user_id: User ID
                    用户 ID
            required_permission: Required permission level
                                所需权限级别
            user_role: User's role
                      用户角色
        Returns:
            List of accessible document IDs
            可访问的文档 ID 列表
        """
        return [
            doc_id
            for doc_id in document_ids
            if self.check_permission(doc_id, user_id, required_permission, user_role)
        ]


# Global permission service instance
# 全局权限服务实例
permission_service = PermissionService()
