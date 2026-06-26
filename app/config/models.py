"""
Configuration data models and input validation logic.
"""

from typing import Optional, Set
from pydantic import BaseModel, Field, field_validator


class AppSettings(BaseModel):
    """Configuration settings related to application metadata and environment."""
    name: str = Field(..., description="The name of the application.")
    version: str = Field(..., description="The version of the application.")
    api_version: str = Field(..., description="The API version prefix.")
    debug: bool = Field(..., description="Enable or disable debug mode.")
    environment: str = Field(..., description="Deployment environment (e.g. development, production).")


class AISettings(BaseModel):
    """Configuration settings for AI model providers and requests."""
    provider: str = Field(..., description="AI provider to use (gemini, openai, claude).")
    api_key: Optional[str] = Field(None, description="API Key for the chosen AI provider.")
    default_model: str = Field(..., description="Default model name for the AI provider.")
    request_timeout_seconds: int = Field(..., description="Timeout in seconds for AI requests.")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that the provider is supported."""
        allowed = {"gemini", "openai", "claude"}
        val = v.strip().lower()
        if val not in allowed:
            raise ValueError(f"AI_PROVIDER must be one of: {', '.join(allowed)}")
        return val


class UploadSettings(BaseModel):
    """Configuration settings for file upload and extraction limits."""
    max_upload_size_mb: int = Field(..., description="Maximum allowed size of upload files in MB.")
    max_extraction_files: int = Field(..., description="Maximum number of files allowed in extraction.")
    max_file_size_mb: int = Field(..., description="Maximum size of an individual file in extraction in MB.")

    @field_validator("max_upload_size_mb", "max_extraction_files", "max_file_size_mb")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that limit values are strictly positive."""
        if v <= 0:
            raise ValueError("Configuration limits must be greater than 0")
        return v


class LoggingSettings(BaseModel):
    """Configuration settings for system logging."""
    log_level: str = Field(..., description="Logging severity level.")
    log_format: str = Field(..., description="Standard format string for log messages.")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that the logging level is standard and recognized."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        val = v.strip().upper()
        if val not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(allowed)}")
        return val
