from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    # For local development with SQLite: sqlite+aiosqlite:///./ai_context_bridge.db
    # For Google Cloud with PostgreSQL: postgresql+asyncpg://...
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_context_bridge.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 150

    # API Settings
    CORS_ORIGINS: List[str] = [
        "chrome-extension://*",  # Allow all Chrome extensions
        "http://localhost",
        "http://localhost:*",
    ]
    MAX_CONTEXT_SIZE: int = 1000000  # 1MB in characters
    MAX_MESSAGES_PER_CONTEXT: int = 500
    DEFAULT_RETENTION_DAYS: int = 30

    # Rate Limiting (no auth, so IP-based)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds

    # Server
    PORT: int = 8000
    WORKERS: int = 4
    LOG_LEVEL: str = "info"

    # Environment
    ENV: str = "development"  # development, production

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
