"""
Settings loading and management using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.models import AISettings, AppSettings, LoggingSettings, UploadSettings
from app.core import constants


class SettingsLoader(BaseSettings):
    """Flat environment variable loader using Pydantic Settings."""

    # App Settings
    app_name: str = Field(default=constants.APP_NAME, validation_alias="APP_NAME")
    app_version: str = Field(default=constants.APP_VERSION, validation_alias="APP_VERSION")
    api_version: str = Field(default=constants.API_VERSION, validation_alias="API_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # AI Settings
    ai_provider: str = Field(default="gemini", validation_alias="AI_PROVIDER")
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    default_model: str = Field(default=constants.DEFAULT_MODEL, validation_alias="DEFAULT_MODEL")
    request_timeout_seconds: int = Field(default=60, validation_alias="REQUEST_TIMEOUT_SECONDS")

    # Upload Settings
    max_upload_size_mb: int = Field(default=constants.MAX_UPLOAD_SIZE_MB, validation_alias="MAX_UPLOAD_SIZE_MB")
    max_extraction_files: int = Field(default=5000, validation_alias="MAX_EXTRACTION_FILES")
    max_file_size_mb: int = Field(default=10, validation_alias="MAX_FILE_SIZE_MB")

    # Logging Settings
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default=constants.DEFAULT_LOG_FORMAT, validation_alias="LOG_FORMAT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings:
    """Application Settings container holding structured configurations."""

    def __init__(self, loader: SettingsLoader) -> None:
        self.app = AppSettings(
            name=loader.app_name,
            version=loader.app_version,
            api_version=loader.api_version,
            debug=loader.debug,
            environment=loader.environment,
        )
        self.ai = AISettings(
            provider=loader.ai_provider,
            api_key=loader.gemini_api_key,
            default_model=loader.default_model,
            request_timeout_seconds=loader.request_timeout_seconds,
        )
        self.upload = UploadSettings(
            max_upload_size_mb=loader.max_upload_size_mb,
            max_extraction_files=loader.max_extraction_files,
            max_file_size_mb=loader.max_file_size_mb,
        )
        self.logging = LoggingSettings(
            log_level=loader.log_level,
            log_format=loader.log_format,
        )


@lru_cache
def get_settings() -> Settings:
    """
    Get the cached application settings.
    Settings are loaded once and cached using @lru_cache.
    """
    # Check if .env.local exists, otherwise default to .env
    env_file = ".env"
    if Path(".env.local").exists():
        env_file = ".env.local"

    loader = SettingsLoader(_env_file=env_file)
    return Settings(loader)
