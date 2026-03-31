"""
Authentication service for user management and JWT token handling
用户管理和 JWT token 处理的认证服务

Day 6: Security & Governance
Day 6： 安全与治理
"""

import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid

from config import settings, get_logger

logger = get_logger(__name__)


# Password hashing context
# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class User:
    """
    User model for authentication
    认证用户模型

    Day 6: New model for user management
    Day 6： 用户管理的新模型
    """
    id: str
    username: str
    email: str
    hashed_password: str
    role: str = "user"  # "admin", "user", "viewer"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (without password)
        将用户转换为字典（不包含密码）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


@dataclass
class TokenData:
    """
    Token payload data
    Token 负载数据

    Day 6: New model for JWT token data
    Day 6： JWT token 数据的新模型
    """
    user_id: str
    username: str
    role: str
    exp: datetime


class AuthService:
    """
    Authentication service for user management
    用户管理的认证服务

    Day 6: New service for JWT authentication
    Day 6： JWT 认证的新服务

    Features:
    - User registration and login
    - JWT token generation and validation
    - Password hashing and verification
    - In-memory user storage (for demo, replace with database in production)
    """

    def __init__(self):
        # In-memory user storage (for demo purposes)
        # 内存用户存储（用于演示目的）
        # In production, replace with database storage
        # 生产环境中，替换为数据库存储
        self._users: Dict[str, User] = {}
        self._users_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "users.json")
        self._load_users()

        # Create default admin user if no users exist
        # 如果没有用户则创建默认管理员
        if not self._users:
            self._create_default_admin()

    def _load_users(self):
        """Load users from file
        从文件加载用户"""
        try:
            if os.path.exists(self._users_file):
                with open(self._users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_data in data.get("users", []):
                        user = User(
                            id=user_data["id"],
                            username=user_data["username"],
                            email=user_data["email"],
                            hashed_password=user_data["hashed_password"],
                            role=user_data.get("role", "user"),
                            is_active=user_data.get("is_active", True),
                            created_at=datetime.fromisoformat(user_data["created_at"]) if user_data.get("created_at") else datetime.now(),
                            last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                        )
                        self._users[user.id] = user
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            # Initialize with empty dict if loading fails
            # 如果加载失败则初始化为空字典
            self._users = {}

    def _save_users(self):
        """Save users to file
        保存用户到文件"""
        try:
            # Create data directory if not exists
            # 如果数据目录不存在则创建
            os.makedirs(os.path.dirname(self._users_file), exist_ok=True)

            data = {
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "hashed_password": user.hashed_password,
                        "role": user.role,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                    }
                    for user in self._users.values()
                ]
            }

            with open(self._users_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")

    def _create_default_admin(self):
        """Create default admin user
        创建默认管理员用户"""
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@example.com",
            hashed_password=self.hash_password("admin123"),
            role="admin",
            is_active=True,
        )
        self._users[admin_user.id] = admin_user
        self._save_users()
        logger.info("Created default admin user: admin / admin123")

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        使用 bcrypt 哈希密码

        Args:
            password: Plain text password
                      明文密码
        Returns:
            Hashed password
            哈希后的密码
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        验证密码与哈希是否匹配

        Args:
            plain_password: Plain text password
                           明文密码
            hashed_password: Hashed password to compare
                            要比较的哈希密码
        Returns:
            True if password matches
            如果密码匹配则返回 True
        """
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        """
        Create a JWT access token for a user
        为用户创建 JWT 访问 token

        Args:
            user: User to create token for
                  要创建 token 的用户
        Returns:
            JWT access token string
            JWT 访问 token 字符串
        """
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return token

    def decode_token(self, token: str) -> Optional[TokenData]:
        """
        Decode and validate a JWT token
        解码并验证 JWT token

        Args:
            token: JWT token string
                   JWT token 字符串
        Returns:
            TokenData if valid, None if invalid
            如果有效返回 TokenData，无效返回 None
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )

            return TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                role=payload.get("role"),
                exp=datetime.fromtimestamp(payload.get("exp")),
            )
        except JWTError:
            return None

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> User:
        """
        Register a new user
        注册新用户

        Args:
            username: Username for new user
                     新用户的用户名
            email: Email for new user
                  新用户的邮箱
            password: Plain text password
                     明文密码
            role: User role (admin, user, viewer)
                 用户角色（admin, user, viewer）
        Returns:
            Created User object
            创建的 User 对象
        Raises:
            ValueError: If username or email already exists
                       如果用户名或邮箱已存在
        """
        # Check if username exists
        # 检查用户名是否存在
        for user in self._users.values():
            if user.username == username:
                raise ValueError(f"Username '{username}' already exists")
            if user.email == email:
                raise ValueError(f"Email '{email}' already exists")

        # Validate password length
        # 验证密码长度
        if len(password) < settings.password_min_length:
            raise ValueError(f"Password must be at least {settings.password_min_length} characters")

        # Create new user
        # 创建新用户
        new_user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=self.hash_password(password),
            role=role,
            is_active=True,
        )

        self._users[new_user.id] = new_user
        self._save_users()

        return new_user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password
        通过用户名和密码验证用户

        Args:
            username: Username to authenticate
                     要验证的用户名
            password: Plain text password
                     明文密码
        Returns:
            User if authentication successful, None otherwise
            如果验证成功返回 User，否则返回 None
        """
        # Find user by username
        # 通过用户名查找用户
        user = None
        for u in self._users.values():
            if u.username == username:
                user = u
                break

        if not user:
            return None

        # Check if user is active
        # 检查用户是否活跃
        if not user.is_active:
            return None

        # Verify password
        # 验证密码
        if not self.verify_password(password, user.hashed_password):
            return None

        # Update last login time
        # 更新最后登录时间
        user.last_login = datetime.now()
        self._save_users()

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID
        通过 ID 获取用户

        Args:
            user_id: User ID
                    用户 ID
        Returns:
            User if found, None otherwise
            如果找到返回 User，否则返回 None
        """
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username
        通过用户名获取用户

        Args:
            username: Username to find
                     要查找的用户名
        Returns:
            User if found, None otherwise
            如果找到返回 User，否则返回 None
        """
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get_all_users(self) -> list[User]:
        """
        Get all users
        获取所有用户

        Returns:
            List of all users
            所有用户的列表
        """
        return list(self._users.values())

    def update_user_role(self, user_id: str, role: str) -> Optional[User]:
        """
        Update a user's role
        更新用户角色

        Args:
            user_id: User ID
                    用户 ID
            role: New role (admin, user, viewer)
                 新角色（admin, user, viewer）
        Returns:
            Updated User if found, None otherwise
            如果找到返回更新的 User，否则返回 None
        """
        user = self._users.get(user_id)
        if user:
            user.role = role
            self._save_users()
        return user

    def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user (soft delete)
        停用用户（软删除）

        Args:
            user_id: User ID
                    用户 ID
        Returns:
            Updated User if found, None otherwise
            如果找到返回更新的 User，否则返回 None
        """
        user = self._users.get(user_id)
        if user:
            user.is_active = False
            self._save_users()
        return user

    def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a user
        激活用户

        Args:
            user_id: User ID
                    用户 ID
        Returns:
            Updated User if found, None otherwise
            如果找到返回更新的 User，否则返回 None
        """
        user = self._users.get(user_id)
        if user:
            user.is_active = True
            self._save_users()
        return user


# Global auth service instance
# 全局认证服务实例
auth_service = AuthService()
