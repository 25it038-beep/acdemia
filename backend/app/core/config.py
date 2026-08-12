from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "Academia AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"

    # Dev: skip Clerk JWT checks and auto-login a private dev user
    # (never a shared demo account — each env has its own isolated user)
    AUTH_BYPASS: bool = False
    AUTH_BYPASS_EMAIL: str = "dev@academia.ai"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://academia:academia@localhost:5432/academia"
    REDIS_URL: str = "redis://localhost:6379/0"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "academia"
    QDRANT_URL: str = "http://localhost:6333"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "academia"
    MINIO_SECRET_KEY: str = "academia123"
    MINIO_BUCKET: str = "academia-uploads"

    # Auth
    SECRET_KEY: str = "academia-ai-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Clerk — replaces self-issued JWT auth
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_ISSUER: str = "https://natural-cat-23.clerk.accounts.dev"

    # AI Provider — NVIDIA only. No alternate provider is supported.
    AI_PROVIDER: str = "nvidia"
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_CODING_API_KEY: Optional[str] = None
    NVIDIA_VISION_API_KEY: Optional[str] = None
    NVIDIA_EMBED_API_KEY: Optional[str] = None
    NVIDIA_RIVA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Per-task models (NVIDIA)
    CHAT_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    STEM_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    CODING_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    VISION_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    EMBEDDING_MODEL: str = "nvidia/nv-embedqa-e5-v5"
    RERANK_MODEL: str = "nvidia/nv-embedqa-e5-v5"

    # Embedding
    EMBEDDING_DIMENSION: int = 1024

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB per chunk
    CHUNK_SIZE: int = 50 * 1024 * 1024  # 50MB chunks
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".pptx", ".ppt", ".xlsx", ".csv",
        ".txt", ".md", ".epub", ".zip", ".html", ".htm",
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
        ".mp4", ".avi", ".mov", ".mkv", ".webm",
        ".mp3", ".wav", ".ogg", ".m4a", ".flac",
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp",
        ".c", ".h", ".rb", ".go", ".rs", ".swift", ".kt",
    ]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090

    class Config:
        env_file = str(_ENV_FILE)
        case_sensitive = True


settings = Settings()