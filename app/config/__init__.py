"""
app/config – Centralised configuration, logging setup, and logger factory.

Public API (import from here, not from sub-modules):
  get_settings()      → cached Settings object loaded from .env / .env.local
  configure_logging() → call once at startup to wire Python logging
  get_logger(name)    → get a named logger (pass __name__ from your module)
"""

from app.config.logging import configure_logging, get_logger
from app.config.settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
    "configure_logging",
    "get_logger",
]
