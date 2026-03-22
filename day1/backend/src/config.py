"""
Configuration management for the RAG application
RAG 应用的配置管理
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
# 从 .env 文件加载环境变量
load_dotenv()


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


# Global settings instance
# 全局设置实例
settings = Settings()
