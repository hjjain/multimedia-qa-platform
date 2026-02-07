"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Replicate API (for LLM + Whisper)
    replicate_api_token: str = ""

    # Model configuration
    llm_model: str = "openai/gpt-5.2"
    whisper_model: str = "openai/whisper"

    # MongoDB
    mongodb_url: str = "mongodb://mongodb:27017"
    mongodb_db_name: str = "panscience"

    # Redis
    redis_url: str = "redis://redis:6379"

    # App settings
    max_file_size_mb: int = 100
    allowed_extensions: List[str] = [
        "pdf", "mp3", "wav", "mp4", "webm", "m4a"
    ]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
