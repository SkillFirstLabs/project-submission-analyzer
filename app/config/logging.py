"""
Logging configuration and logger factory for the application.

This module provides two public functions:
  - configure_logging(): Called once at app startup to set up handlers/formatters.
  - get_logger(name): Called by every module to get a named logger instance.
"""

import logging
import logging.config
import sys
from typing import Any, Dict


def configure_logging() -> None:
    """
    Configure application-wide logging from settings.

    Reads LOG_LEVEL and LOG_FORMAT from the active settings and applies
    a consistent dictConfig that covers the root logger, uvicorn, and
    the app.* namespace.

    Should be called exactly once, early in application startup (main.py).
    """
    # Import here to avoid circular imports at module load time
    from app.config.settings import get_settings

    settings = get_settings()
    log_level = settings.logging.log_level.upper()
    log_format = settings.logging.log_format

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            # Silence uvicorn's own log propagation to avoid duplicates
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            # All app.* loggers inherit this level
            "app": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger instance.

    Args:
        name: Logger name — use the module's dotted path (e.g. 'app.api.routes').
              Conventionally pass __name__ from the calling module.

    Returns:
        A standard logging.Logger configured by configure_logging().

    Example:
        logger = get_logger(__name__)
        logger.info("Server started")
    """
    return logging.getLogger(name)
