"""
Google Gemini API LLM client with automatic key rotation and async execution.

Rotation strategy:
- Maintains a list of all configured API keys
- Tries the current key first
- On quota (429), rate-limit, or auth errors (401/403/400 invalid key) → rotates to the next key
- Tries every key before giving up
- Tracks which key index is active so it persists across calls within a request
"""

import asyncio
import google.generativeai as genai
from google.api_core.exceptions import (
    GoogleAPIError,
    ResourceExhausted,
    ServiceUnavailable,
    PermissionDenied,
    Unauthenticated,
    InvalidArgument,
)

from app.llm.base import BaseLLMClient, LLMResponse
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Errors that should trigger key rotation
_ROTATABLE_ERRORS = (ResourceExhausted, ServiceUnavailable, PermissionDenied, Unauthenticated)


class GeminiClient(BaseLLMClient):
    """
    Gemini client with round-robin key rotation on quota/auth failures.

    Thread-safe & async-safe: uses an asyncio.Lock to serialize key configuration
    and API call execution to prevent race conditions in concurrent requests.
    """

    def __init__(self):
        settings = get_settings()
        self._keys = settings.gemini_api_key_list
        self._model_name = settings.gemini_model
        self._current_index = 0
        self._lock = asyncio.Lock()

        if not self._keys:
            logger.warning(
                "No Gemini API keys configured. "
                "Set GEMINI_API_KEYS in .env (comma-separated)."
            )
        else:
            logger.info("Gemini client initialised", extra={
                "model": self._model_name,
                "key_count": len(self._keys),
            })

    def is_available(self) -> bool:
        return len(self._keys) > 0

    def _get_model(self, key_index: int) -> genai.GenerativeModel:
        """Configure genai with the key at the given index and return a model."""
        genai.configure(api_key=self._keys[key_index])
        return genai.GenerativeModel(self._model_name)

    async def _advance_key(self) -> int:
        """Async-safely rotate to the next key. Returns the new index."""
        async with self._lock:
            self._current_index = (self._current_index + 1) % len(self._keys)
            return self._current_index

    async def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        if not self.is_available():
            raise RuntimeError(
                "No Gemini API keys configured. "
                "Set GEMINI_API_KEYS in .env"
            )

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        num_keys = len(self._keys)

        # Try every key before giving up
        for attempt in range(num_keys):
            async with self._lock:
                index = self._current_index

            key_label = f"key[{index + 1}/{num_keys}]"
            try:
                # Configure key and perform the async API call under the lock
                async with self._lock:
                    model = self._get_model(index)
                    response = await model.generate_content_async(full_prompt)
                
                text = response.text or ""

                tokens_used = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    tokens_used = (
                        getattr(response.usage_metadata, "total_token_count", 0) or 0
                    )

                logger.info("Gemini generation succeeded", extra={
                    "key_index": index + 1,
                    "tokens_used": tokens_used,
                    "response_length": len(text),
                })
                return LLMResponse(
                    text=text,
                    tokens_used=tokens_used,
                    provider=f"gemini:{self._model_name}",
                )

            except _ROTATABLE_ERRORS as exc:
                logger.warning(
                    f"Gemini {key_label} hit a quota/auth error — rotating key. "
                    f"Error: {type(exc).__name__}: {exc}"
                )
                new_index = await self._advance_key()
                logger.info(f"Rotated to key[{new_index + 1}/{num_keys}]")

            except InvalidArgument as exc:
                # Treat invalid API key arguments as rotatable
                err_msg = str(exc)
                if "API key not valid" in err_msg or "API_KEY" in err_msg or "invalid" in err_msg.lower():
                    logger.warning(
                        f"Gemini {key_label} hit invalid key error — rotating key. "
                        f"Error: InvalidArgument: {exc}"
                    )
                    new_index = await self._advance_key()
                    logger.info(f"Rotated to key[{new_index + 1}/{num_keys}]")
                else:
                    logger.error(f"Gemini {key_label} true invalid argument error: {exc}")
                    raise RuntimeError(f"Gemini API error: {exc}") from exc

            except GoogleAPIError as exc:
                # Non-rotatable API error (e.g. invalid prompt, content policy)
                logger.error(f"Gemini {key_label} non-rotatable error: {exc}")
                raise RuntimeError(f"Gemini API error: {exc}") from exc

            except Exception as exc:
                logger.error(f"Gemini {key_label} unexpected error: {exc}")
                raise RuntimeError(f"Unexpected Gemini error: {exc}") from exc

        # All keys exhausted
        raise RuntimeError(
            f"All {num_keys} Gemini API key(s) are exhausted or invalid. "
            "Check your quotas and key configuration."
        )
