"""
Cache service for performance optimization
用于性能优化的缓存服务

Day 7: Production optimization - Caching layer
Day 7： 生产优化 - 缓存层
"""

import hashlib
import json
from typing import Any, Optional, Callable
from datetime import timedelta
from functools import wraps
import asyncio
from cachetools import TTLCache, cached
import logging

from config import settings

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service with TTL support for query and embedding results
    带有 TTL 支持的查询和嵌入结果缓存服务

    Provides:
    - In-memory caching with configurable TTL
    - Optional Redis support for distributed caching
    - Automatic cache invalidation
    """

    def __init__(self):
        """Initialize cache service / 初始化缓存服务"""
        self._enabled = settings.cache_enabled
        self._ttl = settings.cache_ttl_seconds
        self._max_size = settings.cache_max_size

        # In-memory cache
        # 内存缓存
        self._cache: TTLCache = TTLCache(
            maxsize=self._max_size,
            ttl=self._ttl
        )

        # Redis client (optional)
        # Redis 客户端（可选）
        self._redis_client = None

        if settings.redis_url:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(settings.redis_url)
                logger.info(f"Redis cache connected: {settings.redis_url}")
                logger.info(f"Redis 缓存已连接: {settings.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                logger.warning(f"连接 Redis 失败: {e}")

        logger.info(f"Cache service initialized (enabled={self._enabled}, ttl={self._ttl}s)")
        logger.info(f"缓存服务已初始化 (启用={self._enabled}, TTL={self._ttl}秒)")

    @staticmethod
    def _generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments
        从参数生成缓存键

        Args:
            prefix: Key prefix for namespace
                    键前缀，用于命名空间
            *args: Positional arguments
                   位置参数
            **kwargs: Keyword arguments
                      关键字参数

        Returns:
            Hashed cache key
            哈希后的缓存键
        """
        # Create a string representation of arguments
        # 创建参数的字符串表示
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        从缓存获取值

        Args:
            key: Cache key
                 缓存键

        Returns:
            Cached value or None
            缓存值或 None
        """
        if not self._enabled:
            return None

        # Try Redis first if available
        # 如果可用，先尝试 Redis
        if self._redis_client:
            try:
                value = await self._redis_client.get(key)
                if value:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # Fallback to in-memory cache
        # 回退到内存缓存
        value = self._cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit (memory): {key}")
        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        设置缓存值

        Args:
            key: Cache key
                 缓存键
            value: Value to cache
                   要缓存的值
            ttl: Time to live in seconds (optional)
                 生存时间（秒），可选

        Returns:
            True if successful
            成功返回 True
        """
        if not self._enabled:
            return False

        ttl = ttl or self._ttl

        # Set in Redis if available
        # 如果可用，设置到 Redis
        if self._redis_client:
            try:
                await self._redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # Set in memory cache
        # 设置到内存缓存
        self._cache[key] = value
        logger.debug(f"Cache set: {key}")
        return True

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        从缓存删除值

        Args:
            key: Cache key
                 缓存键

        Returns:
            True if deleted
            删除成功返回 True
        """
        if not self._enabled:
            return False

        # Delete from Redis
        # 从 Redis 删除
        if self._redis_client:
            try:
                await self._redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")

        # Delete from memory
        # 从内存删除
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
            return True
        return False

    async def clear(self) -> None:
        """
        Clear all cache entries
        清除所有缓存条目
        """
        # Clear memory cache
        # 清除内存缓存
        self._cache.clear()

        # Clear Redis if available
        # 如果可用，清除 Redis
        if self._redis_client:
            try:
                await self._redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")

        logger.info("Cache cleared")
        logger.info("缓存已清除")

    async def get_stats(self) -> dict:
        """
        Get cache statistics
        获取缓存统计

        Returns:
            Dictionary with cache statistics
            包含缓存统计的字典
        """
        return {
            "enabled": self._enabled,
            "ttl_seconds": self._ttl,
            "max_size": self._max_size,
            "current_size": len(self._cache),
            "redis_connected": self._redis_client is not None,
        }

    def cached_query(self, prefix: str = "query"):
        """
        Decorator for caching query results
        用于缓存查询结果的装饰器

        Args:
            prefix: Cache key prefix
                    缓存键前缀

        Usage:
            @cache_service.cached_query("embedding")
            async def get_embedding(text: str) -> list:
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)

                key = self._generate_key(prefix, *args, **kwargs)

                # Try to get from cache
                # 尝试从缓存获取
                cached_result = await self.get(key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                # 执行函数并缓存结果
                result = await func(*args, **kwargs)
                await self.set(key, result)
                return result

            return wrapper
        return decorator


# Global cache service instance
# 全局缓存服务实例
cache_service = CacheService()
