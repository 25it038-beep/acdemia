from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    APP_NAME: str = "Academia AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"

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

    # AI Provider (primary: NVIDIA NIM, fallbacks)
    AI_PROVIDER: str = "nvidia"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_CODING_API_KEY: Optional[str] = None
    NVIDIA_VISION_API_KEY: Optional[str] = None
    NVIDIA_EMBED_API_KEY: Optional[str] = None
    NVIDIA_RIVA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Per-task models (confirmed working on NVIDIA NIM)
    CHAT_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    STEM_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    CODING_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    VISION_MODEL: str = "meta/llama-3.2-90b-vision-instruct"
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
        env_file = ".env"
        case_sensitive = True


settings = Settings()