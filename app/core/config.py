"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # LLM provider
    llm_provider: str = Field(default="gemini", pattern="^(gemini|local)$")

    # Gemini — accepts a comma-separated list of API keys for rotation
    gemini_api_keys: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")

    # Local LLM
    local_llm_base_url: str = Field(default="http://localhost:11434")
    local_llm_model: str = Field(default="llama3")

    # Upload limits
    max_zip_size_mb: int = Field(default=50, gt=0)
    max_uncompressed_size_mb: int = Field(default=500, gt=0)
    max_file_count: int = Field(default=1000, gt=0)
    max_single_file_size_mb: int = Field(default=1, gt=0)

    # Analysis
    default_questions_per_skill: int = Field(default=3, gt=0)
    confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # Logging
    log_level: str = Field(default="INFO")

    # Derived byte limits (computed properties)
    @property
    def max_zip_size_bytes(self) -> int:
        return self.max_zip_size_mb * 1024 * 1024

    @property
    def max_uncompressed_size_bytes(self) -> int:
        return self.max_uncompressed_size_mb * 1024 * 1024

    @property
    def max_single_file_size_bytes(self) -> int:
        return self.max_single_file_size_mb * 1024 * 1024

    @property
    def gemini_api_key_list(self) -> list[str]:
        """Return a cleaned list of all configured Gemini API keys."""
        return [
            k.strip()
            for k in self.gemini_api_keys.split(",")
            if k.strip()
        ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Call this after changing .env at runtime to force reload."""
    get_settings.cache_clear()
