"""
Application configuration using pydantic-settings.

Note: pydantic v2 / pydantic-settings v2 dropped the v1-style
Field(env="...") kwarg. Per-field environment variable names are now
declared via `validation_alias`, while `SettingsConfigDict` controls
file-level behavior (env file path, case sensitivity, etc).
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="127.0.0.1", validation_alias="REPODOC_HOST")
    port: int = Field(default=8765, validation_alias="REPODOC_PORT")
    env: str = Field(default="production", validation_alias="REPODOC_ENV")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="REPODOC_LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, validation_alias="REPODOC_LOG_FILE")

    # AI
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    ai_model: str = Field(default="claude-3-5-haiku-20241022", validation_alias="REPODOC_AI_MODEL")
    ai_enabled: bool = Field(default=True, validation_alias="REPODOC_AI_ENABLED")

    # Paths
    temp_dir: Path = Field(
        default_factory=lambda: Path(os.path.expanduser("~/.repodoc/temp")),
        validation_alias="REPODOC_TEMP_DIR",
    )
    output_dir: Path = Field(
        default_factory=lambda: Path(os.path.expanduser("~/Documents/RepoDoc")),
        validation_alias="REPODOC_OUTPUT_DIR",
    )

    # Performance
    max_file_size_mb: int = Field(default=50, validation_alias="REPODOC_MAX_FILE_SIZE_MB")
    max_concurrent_workers: int = Field(default=4, validation_alias="REPODOC_MAX_WORKERS")
    scan_chunk_size: int = Field(default=500, validation_alias="REPODOC_SCAN_CHUNK_SIZE")

    # PDF
    pdf_engine: str = Field(default="reportlab", validation_alias="REPODOC_PDF_ENGINE")

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
