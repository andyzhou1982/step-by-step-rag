"""
Retry service for resilient API calls
用于弹性 API 调用的重试服务

Day 7: Production optimization - Retry logic
Day 7： 生产优化 - 重试逻辑
"""

import asyncio
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps
import random

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from config import settings

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryService:
    """
    Retry service with exponential backoff for API calls
    带有指数退避的 API 调用重试服务

    Provides:
    - Configurable retry attempts
    - Exponential backoff with jitter
    - Retry on specific exceptions
    """

    def __init__(self):
        """Initialize retry service / 初始化重试服务"""
        self._max_attempts = settings.retry_max_attempts
        self._backoff_factor = settings.retry_backoff_factor
        self._max_wait = settings.retry_max_wait_seconds

        logger.info(
            f"Retry service initialized (max_attempts={self._max_attempts}, "
            f"backoff_factor={self._backoff_factor})"
        )
        logger.info(
            f"重试服务已初始化 (最大尝试次数={self._max_attempts}, "
            f"退避因子={self._backoff_factor})"
        )

    def get_retry_decorator(
        self,
        max_attempts: Optional[int] = None,
        exception_types: tuple = (Exception,),
        on_retry: Optional[Callable] = None
    ) -> Callable:
        """
        Get a configured retry decorator
        获取配置好的重试装饰器

        Args:
            max_attempts: Maximum retry attempts (default from settings)
                          最大重试次数（默认从设置获取）
            exception_types: Exception types to retry on
                             需要重试的异常类型
            on_retry: Callback function called on each retry
                      每次重试时调用的回调函数

        Returns:
            Configured retry decorator
            配置好的重试装饰器
        """
        attempts = max_attempts or self._max_attempts

        return retry(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(
                multiplier=self._backoff_factor,
                max=self._max_wait
            ),
            retry=retry_if_exception_type(exception_types),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        max_attempts: Optional[int] = None,
        exception_types: tuple = (Exception,),
        **kwargs
    ) -> T:
        """
        Execute a function with retry logic
        使用重试逻辑执行函数

        Args:
            func: Async function to execute
                  要执行的异步函数
            *args: Positional arguments for the function
                   函数的位置参数
            max_attempts: Maximum retry attempts
                          最大重试次数
            exception_types: Exception types to retry on
                             需要重试的异常类型
            **kwargs: Keyword arguments for the function
                      函数的关键字参数

        Returns:
            Function result
            函数结果

        Raises:
            Last exception if all retries fail
            如果所有重试失败则抛出最后的异常
        """
        attempts = max_attempts or self._max_attempts
        last_exception = None

        for attempt in range(1, attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except exception_types as e:
                last_exception = e

                if attempt < attempts:
                    # Calculate wait time with exponential backoff and jitter
                    # 计算带有指数退避和抖动的等待时间
                    wait_time = min(
                        self._backoff_factor ** (attempt - 1) + random.uniform(0, 1),
                        self._max_wait
                    )

                    logger.warning(
                        f"Retry attempt {attempt}/{attempts} after {wait_time:.2f}s "
                        f"due to: {type(e).__name__}: {str(e)}"
                    )
                    logger.warning(
                        f"重试尝试 {attempt}/{attempts}，等待 {wait_time:.2f}秒 "
                        f"原因: {type(e).__name__}: {str(e)}"
                    )

                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"All {attempts} retry attempts failed. Last error: {str(e)}"
                    )
                    logger.error(
                        f"所有 {attempts} 次重试尝试失败。最后错误: {str(e)}"
                    )

        raise last_exception


def with_retry(
    max_attempts: Optional[int] = None,
    exception_types: tuple = (Exception,)
):
    """
    Decorator for adding retry logic to functions
    为函数添加重试逻辑的装饰器

    Args:
        max_attempts: Maximum retry attempts
                      最大重试次数
        exception_types: Exception types to retry on
                         需要重试的异常类型

    Usage:
        @with_retry(max_attempts=3, exception_types=(ConnectionError,))
        async def call_external_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            retry_service = RetryService()
            return await retry_service.execute_with_retry(
                func,
                *args,
                max_attempts=max_attempts,
                exception_types=exception_types,
                **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            retry_service = RetryService()
            decorator = retry_service.get_retry_decorator(
                max_attempts=max_attempts,
                exception_types=exception_types
            )
            return decorator(func)(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Common exception types for API retries
# API 重试的常见异常类型
API_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


# Global retry service instance
# 全局重试服务实例
retry_service = RetryService()
