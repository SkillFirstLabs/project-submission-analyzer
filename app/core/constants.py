"""
Constants module containing application-wide global constants.
"""

from typing import Set

# Schema Version
SCHEMA_VERSION: str = "1.0"

# Application Metadata
APP_NAME: str = "Project Submission AI Analyzer"
APP_VERSION: str = "1.0.0"
API_VERSION: str = "v1"

# Defaults
DEFAULT_QUESTIONS_PER_SKILL: int = 2
DEFAULT_MODEL: str = "gemini-2.5-flash"
DEFAULT_LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Limits
MAX_UPLOAD_SIZE_MB: int = 100

# Supported Archives
SUPPORTED_ARCHIVE_EXTENSIONS: Set[str] = {".zip"}
