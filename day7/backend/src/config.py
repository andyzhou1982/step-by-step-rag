"""
Configuration management for the RAG application
RAG 应用的配置管理

Day 3: Added retrieval configuration
Day 3： 添加了检索配置

Day 4: Added streaming and context configuration
Day 4： 添加了流式输出和上下文配置

Day 5: Added evaluation and tracing configuration
Day 5： 添加了评估和追踪配置

Day 6: Added security and authentication configuration
Day 6： 添加了安全和认证配置

Day 7: Added production and performance configuration
Day 7： 添加了生产和性能配置
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
# 从 .env 文件加载环境变量
# Try multiple locations to find .env file
# 尝试多个位置查找 .env 文件
env_paths = [
    Path(__file__).parent.parent / ".env",  # backend/.env (when running from src/)
    Path(__file__).parent / ".env",          # src/.env
    Path.cwd() / ".env",                     # current working directory
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break


def setup_logging(
    level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None
) -> None:
    """
    Setup unified logging configuration for the entire application
    为整个应用设置统一的日志配置
    """
    log_level = os.getenv("LOG_LEVEL", level).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers,
        force=True
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class Settings:
    """
    Application settings loaded from environment variables
    从环境变量加载的应用设置
    """

    def __init__(self):
        # OpenAI API Configuration
        # OpenAI API 配置
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_api_base: Optional[str] = os.getenv("OPENAI_API_BASE")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # Database Configuration
        # 数据库配置
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/rag_db"
        )

        # Server Configuration
        # 服务器配置
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        # RAG Configuration
        # RAG 配置
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.top_k: int = int(os.getenv("TOP_K", "5"))

        # Retrieval Configuration (Day 3)
        # 检索配置（Day 3）
        self.use_hybrid_search: bool = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"
        self.use_query_rewrite: bool = os.getenv("USE_QUERY_REWRITE", "false").lower() == "true"
        self.use_rerank: bool = os.getenv("USE_RERANK", "true").lower() == "true"
        self.vector_weight: float = float(os.getenv("VECTOR_WEIGHT", "0.6"))
        self.bm25_weight: float = float(os.getenv("BM25_WEIGHT", "0.4"))

        # Generation Configuration (Day 4)
        # 生成配置（Day 4）
        self.max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "3000"))
        self.streaming_enabled: bool = os.getenv("STREAMING_ENABLED", "true").lower() == "true"
        self.max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
        self.confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

        # Evaluation Configuration (Day 5)
        # 评估配置（Day 5）
        self.evaluation_enabled: bool = os.getenv("EVALUATION_ENABLED", "true").lower() == "true"
        self.tracing_enabled: bool = os.getenv("TRACING_ENABLED", "true").lower() == "true"
        self.metrics_retention_days: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))

        # Security & Authentication Configuration (Day 6)
        # 安全与认证配置（Day 6）
        self.auth_enabled: bool = os.getenv("AUTH_ENABLED", "true").lower() == "true"
        self.jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        self.password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        self.content_filter_enabled: bool = os.getenv("CONTENT_FILTER_ENABLED", "true").lower() == "true"
        self.audit_log_retention_days: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90"))

        # Production & Performance Configuration (Day 7)
        # 生产与性能配置（Day 7）
        self.cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
        self.cache_max_size: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        self.use_redis: bool = os.getenv("USE_REDIS", "false").lower() == "true"
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.retry_max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
        self.retry_backoff_factor: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "1.0"))
        self.retry_max_wait_seconds: float = float(os.getenv("RETRY_MAX_WAIT_SECONDS", "10.0"))
        self.metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


# Global settings instance
# 全局设置实例
settings = Settings()
