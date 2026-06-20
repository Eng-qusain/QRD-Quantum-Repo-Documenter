"""
Application configuration using pydantic-settings.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = Field(default="127.0.0.1", env="REPODOC_HOST")
    port: int = Field(default=8765, env="REPODOC_PORT")
    env: str = Field(default="production", env="REPODOC_ENV")

    # Logging
    log_level: str = Field(default="INFO", env="REPODOC_LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="REPODOC_LOG_FILE")

    # AI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ai_model: str = Field(default="claude-3-5-haiku-20241022", env="REPODOC_AI_MODEL")
    ai_enabled: bool = Field(default=True, env="REPODOC_AI_ENABLED")

    # Paths
    temp_dir: Path = Field(
        default_factory=lambda: Path(os.path.expanduser("~/.repodoc/temp")),
        env="REPODOC_TEMP_DIR",
    )
    output_dir: Path = Field(
        default_factory=lambda: Path(os.path.expanduser("~/Documents/RepoDoc")),
        env="REPODOC_OUTPUT_DIR",
    )

    # Performance
    max_file_size_mb: int = Field(default=50, env="REPODOC_MAX_FILE_SIZE_MB")
    max_concurrent_workers: int = Field(default=4, env="REPODOC_MAX_WORKERS")
    scan_chunk_size: int = Field(default=500, env="REPODOC_SCAN_CHUNK_SIZE")

    # PDF
    pdf_engine: str = Field(default="reportlab", env="REPODOC_PDF_ENGINE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
