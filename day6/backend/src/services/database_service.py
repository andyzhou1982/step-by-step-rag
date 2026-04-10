"""
Database service for connection and session management
数据库连接和会话管理服务

Day 6 Enhancement: Unified database service using SQLAlchemy
Day 6 增强： 使用 SQLAlchemy 的统一数据库服务
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from config import settings, get_logger

from models.database import Base

logger = get_logger(__name__)


class DatabaseService:
    """
    Unified database service for all tables
    所有表的统一数据库服务

    Manages:
    - Database connection
    - Session factory
    - Table creation
    """

    def __init__(self):
        # Convert postgresql:// to postgresql+asyncpg:// for async support
        # 将 postgresql:// 转换为 postgresql+asyncpg:// 以支持异步
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
        """Connect to database / 连接数据库"""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Disconnect from database / 断开数据库连接"""
        await self._engine.dispose()
        logger.info("Database disconnected")

    async def create_tables(self):
        """Create all tables / 创建所有表"""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """
        Get a new database session
        获取新的数据库会话

        Returns:
            New async session / 新的异步会话
        """
        return self._session_factory()

    @property
    def engine(self):
        """Get the database engine / 获取数据库引擎"""
        return self._engine

    @property
    def session_factory(self):
        """Get the session factory / 获取会话工厂"""
        return self._session_factory


# Global database service instance
# 全局数据库服务实例
db_service = DatabaseService()
