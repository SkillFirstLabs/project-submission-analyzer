import pytest
from pydantic import ValidationError
from app.config.settings import SettingsLoader, Settings
from app.config.models import AISettings, LoggingSettings, UploadSettings


def test_default_settings():
    """Verify that default settings load with expected values."""
    loader = SettingsLoader()
    settings = Settings(loader)

    assert settings.app.name == "Project Submission AI Analyzer"
    assert settings.app.version == "1.0.0"
    assert settings.app.api_version == "v1"
    assert settings.app.debug is False
    assert settings.app.environment == "development"
    assert settings.ai.provider == "gemini"
    assert settings.ai.default_model == "gemini-2.5-flash"
    assert settings.upload.max_upload_size_mb == 100
    assert settings.logging.log_level == "INFO"


def test_invalid_logging_level():
    """Verify that invalid log levels raise a Validation Error."""
    with pytest.raises(ValidationError) as exc_info:
        LoggingSettings(log_level="INVALID", log_format="...")
    assert "LOG_LEVEL must be one of" in str(exc_info.value)


def test_invalid_ai_provider():
    """Verify that unsupported AI providers raise a Validation Error."""
    with pytest.raises(ValidationError) as exc_info:
        AISettings(
            provider="invalid_provider",
            api_key=None,
            default_model="model",
            request_timeout_seconds=60,
        )
    assert "AI_PROVIDER must be one of" in str(exc_info.value)


def test_invalid_limits():
    """Verify that non-positive limits raise a Validation Error."""
    with pytest.raises(ValidationError) as exc_info:
        UploadSettings(
            max_upload_size_mb=-5,
            max_extraction_files=100,
            max_file_size_mb=10,
        )
    assert "Configuration limits must be greater than 0" in str(exc_info.value)
