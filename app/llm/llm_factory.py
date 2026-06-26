"""
LLM factory: returns the configured LLM client based on settings or a
per-request override.
"""

from app.llm.base import BaseLLMClient
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Singletons per provider so we don't re-init on every request
_clients: dict[str, BaseLLMClient] = {}


def _build_client(provider: str) -> BaseLLMClient:
    if provider == "gemini":
        from app.llm.gemini_client import GeminiClient
        client = GeminiClient()
        logger.info("Gemini client ready", extra={
            "keys_configured": len(get_settings().gemini_api_key_list)
        })
        return client
    elif provider == "local":
        from app.llm.local_llm_client import LocalLLMClient
        client = LocalLLMClient()
        logger.info("Local LLM client ready", extra={
            "base_url": get_settings().local_llm_base_url,
            "model": get_settings().local_llm_model,
        })
        return client
    else:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. Valid options: 'gemini', 'local'"
        )


def get_llm_client() -> BaseLLMClient:
    """Return the default LLM client from settings (singleton)."""
    provider = get_settings().llm_provider.lower()
    return get_llm_client_for_provider(provider)


def get_llm_client_for_provider(provider: str) -> BaseLLMClient:
    """Return (or create) a singleton client for the given provider."""
    provider = provider.strip().lower()
    if provider not in _clients:
        _clients[provider] = _build_client(provider)
    return _clients[provider]


def reset_llm_client() -> None:
    """Force all clients to be rebuilt on next call."""
    _clients.clear()
