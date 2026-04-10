"""
Authentication service for user management and JWT token handling
用户管理和 JWT token 处理的认证服务

Day 6: Security & Governance
Day 6： 安全与治理

Day 6 Enhancement: Uses PostgreSQL instead of JSON files
Day 6 增强： 使用 PostgreSQL 替代 JSON 文件
"""

import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings, get_logger
from models.database import AppUser
from services.database_service import db_service

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

    Day 6 Enhancement: Now backed by PostgreSQL database
    Day 6 增强： 现在由 PostgreSQL 数据库支持
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

    @classmethod
    def from_db_model(cls, db_user: AppUser) -> "User":
        """Create User from database model / 从数据库模型创建用户"""
        return cls(
            id=str(db_user.id),
            username=db_user.username,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            role=db_user.role,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
        )


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
    - PostgreSQL database storage
    """

    def __init__(self):
        # No initialization needed - database is managed by db_service
        # 不需要初始化 - 数据库由 db_service 管理
        pass

    async def hash_password(self, password: str) -> str:
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

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
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

    async def create_access_token(self, user: User) -> str:
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

    async def decode_token(self, token: str) -> Optional[TokenData]:
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

    async def register_user(
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
        async with db_service.session_factory() as session:
            # Check if username exists
            # 检查用户名是否存在
            result = await session.execute(
                select(AppUser).where(
                    and_(
                        AppUser.username == username,
                        AppUser.email == email
                    )
                )
            )
            existing = result.first()

            if existing:
                # Check which field conflicts
                # 检查哪个字段冲突
                result = await session.execute(
                    select(AppUser).where(AppUser.username == username)
                )
                if result.first():
                    raise ValueError(f"Username '{username}' already exists")

                result = await session.execute(
                    select(AppUser).where(AppUser.email == email)
                )
                if result.first():
                    raise ValueError(f"Email '{email}' already exists")

            # Validate password length
            # 验证密码长度
            if len(password) < settings.password_min_length:
                raise ValueError(f"Password must be at least {settings.password_min_length} characters")

            # Create new user
            # 创建新用户
            hashed_password = await self.hash_password(password)
            new_user = AppUser(
                id=uuid.uuid4(),
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=role,
                is_active=True,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            logger.info(f"New user registered: {username}")
            return User.from_db_model(new_user)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
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
        async with db_service.session_factory() as session:
            # Find user by username
            # 通过用户名查找用户
            result = await session.execute(
                select(AppUser).where(AppUser.username == username)
            )
            db_user = result.scalar_one_or_none()

            if not db_user:
                return None

            if not db_user.is_active:
                return None

            # Verify password
            # 验证密码
            if not await self.verify_password(password, db_user.hashed_password):
                return None

            # Update last login time
            # 更新最后登录时间
            db_user.last_login = datetime.utcnow()
            await session.commit()
            await session.refresh(db_user)

            return User.from_db_model(db_user)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
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
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        async with db_service.session_factory() as session:
            result = await session.execute(
                select(AppUser).where(AppUser.id == user_uuid)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                return User.from_db_model(db_user)
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
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
        async with db_service.session_factory() as session:
            result = await session.execute(
                select(AppUser).where(AppUser.username == username)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                return User.from_db_model(db_user)
            return None

    async def get_all_users(self) -> list[User]:
        """
        Get all users
        获取所有用户

        Returns:
            List of all users
            所有用户的列表
        """
        async with db_service.session_factory() as session:
            result = await session.execute(select(AppUser))
            db_users = result.scalars().all()
            return [User.from_db_model(u) for u in db_users]

    async def update_user_role(self, user_id: str, role: str) -> Optional[User]:
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
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        async with db_service.session_factory() as session:
            result = await session.execute(
                select(AppUser).where(AppUser.id == user_uuid)
            )
            db_user = result.scalar_one_or_none()

            if db_user:
                db_user.role = role
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"User role updated: {user_id} -> {role}")
                return User.from_db_model(db_user)
            return None

    async def deactivate_user(self, user_id: str) -> Optional[User]:
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
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        async with db_service.session_factory() as session:
            result = await session.execute(
                select(AppUser).where(AppUser.id == user_uuid)
            )
            db_user = result.scalar_one_or_none()

            if db_user:
                db_user.is_active = False
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"User deactivated: {user_id}")
                return User.from_db_model(db_user)
            return None

    async def activate_user(self, user_id: str) -> Optional[User]:
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
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        async with db_service.session_factory() as session:
            result = await session.execute(
                select(AppUser).where(AppUser.id == user_uuid)
            )
            db_user = result.scalar_one_or_none()

            if db_user:
                db_user.is_active = True
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"User activated: {user_id}")
                return User.from_db_model(db_user)
            return None

    async def _create_default_admin(self):
        """
        Create default admin user if no users exist
        如果没有用户则创建默认管理员
        """
        async with db_service.session_factory() as session:
            result = await session.execute(select(AppUser))
            existing = result.first()

            if not existing:
                hashed_password = await self.hash_password("admin123")
                admin_user = AppUser(
                    id=uuid.uuid4(),
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hashed_password,
                    role="admin",
                    is_active=True,
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Created default admin user: admin / admin123")


# Global auth service instance
# 全局认证服务实例
auth_service = AuthService()
