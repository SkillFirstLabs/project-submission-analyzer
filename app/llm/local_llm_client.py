"""
Local LLM client — LM Studio (OpenAI-compatible) with Ollama fallback.

Qwen3 / reasoning model notes:
- LM Studio does NOT honour `"thinking": {"type": "disabled"}` — the model
  always runs a reasoning phase and puts the final answer in `content`.
- We need max_tokens large enough for the think phase to FINISH so that
  `content` is populated. 1024 is too small — 4096 is the safe minimum.
- is_available() is cached for 30s to avoid per-request network probes.
- _extract_text() falls back to reasoning_content as a safety net.
"""

import asyncio
import time
import re
import httpx

from app.llm.base import BaseLLMClient, LLMResponse
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_TIMEOUT = 180.0          # 3 min — Qwen3 reasoning can be slow on large prompts
_AVAILABILITY_TTL = 30.0  # cache is_available result for 30s
_MAX_TOKENS = 4096        # must be large enough for think phase + answer


def _extract_text(message: dict) -> str:
    """
    Extract usable text from a chat completion message.

    Qwen3 via LM Studio puts the final answer in `content` and the chain-of-
    thought in `reasoning_content`.  When max_tokens is large enough `content`
    is always populated; `reasoning_content` is only used as a safety net.
    """
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()

    # Primary path: strip any stray <think>…</think> tags from content
    if content:
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if cleaned:
            return cleaned

    # Fallback: extract the final answer from reasoning_content
    if reasoning:
        logger.debug(
            "content empty — extracting answer from reasoning_content",
            extra={"reasoning_length": len(reasoning)},
        )
        # Look for explicit answer markers first
        for marker in ["Final Answer:", "**Final Answer:**", "Answer:", "**Answer:**"]:
            idx = reasoning.rfind(marker)
            if idx != -1:
                answer = reasoning[idx + len(marker):].strip()
                if len(answer) > 5:
                    return answer
        # Take everything after the last double newline (typically the conclusion)
        parts = reasoning.rsplit("\n\n", 1)
        if len(parts) == 2 and len(parts[1].strip()) > 5:
            return parts[1].strip()
        # Last resort: return the whole reasoning block
        return reasoning

    logger.warning("Both content and reasoning_content are empty — returning empty string")
    return ""


class LocalLLMClient(BaseLLMClient):

    def __init__(self):
        settings = get_settings()
        self._base_url = settings.local_llm_base_url.rstrip("/")
        self._model = settings.local_llm_model
        self._available: bool | None = None
        self._available_checked_at: float = 0.0
        self._lock = asyncio.Lock()
        logger.info("Local LLM client initialised", extra={
            "base_url": self._base_url,
            "model": self._model,
        })

    def is_available(self) -> bool:
        """
        Cached availability check — only hits the network once per 30s.
        Accepts any HTTP response < 500 as "server is up".
        LM Studio sometimes returns 404 on /v1/models but still serves completions.
        """
        now = time.monotonic()
        if self._available is not None and (now - self._available_checked_at) < _AVAILABILITY_TTL:
            logger.debug("LLM availability (cached)", extra={"available": self._available})
            return self._available

        for path in ("/v1/models", "/api/tags", "/"):
            url = f"{self._base_url}{path}"
            try:
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(url)
                    logger.info(f"LLM availability probe {url} → {r.status_code}")
                    if r.status_code < 500:   # 200, 404, 405 all mean server is running
                        self._available = True
                        self._available_checked_at = now
                        return True
            except Exception as exc:
                logger.warning(f"LLM availability probe failed for {url}: {exc}")
                continue

        self._available = False
        self._available_checked_at = now
        logger.warning("Local LLM is NOT reachable — falling back to static analysis")
        return False

    async def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Try /v1/chat/completions first (with thinking disabled), fall back to /api/generate."""
        async with self._lock:
            try:
                return await self._openai_compat_generate(prompt, system_prompt)
            except Exception as e1:
                logger.warning(f"LM Studio /v1/chat/completions failed: {e1} — trying /api/generate")

            try:
                return await self._ollama_generate(prompt, system_prompt)
            except Exception as e2:
                raise RuntimeError(
                    f"Local LLM at {self._base_url} unavailable. "
                    f"Ensure LM Studio is running and '{self._model}' is loaded. Error: {e2}"
                ) from e2

    async def _openai_compat_generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """
        POST /v1/chat/completions.
        Disables Qwen3 thinking mode for much faster JSON responses.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.3,   # lower = more deterministic JSON
            # 4096 tokens — Qwen3 reasoning consumes many tokens before producing
            # content; too small a limit yields an empty content field.
            "max_tokens": _MAX_TOKENS,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "unknown")
        text = _extract_text(message)
        tokens_used = data.get("usage", {}).get("total_tokens", 0) or 0

        if finish_reason == "length":
            logger.warning(
                "LM Studio response truncated by max_tokens — consider increasing _MAX_TOKENS",
                extra={"tokens_used": tokens_used, "max_tokens": _MAX_TOKENS},
            )

        if not text:
            logger.error(
                "LM Studio returned empty text",
                extra={
                    "finish_reason": finish_reason,
                    "content": repr(message.get("content", "")),
                    "reasoning_length": len(message.get("reasoning_content") or ""),
                },
            )

        logger.info("LM Studio generation complete", extra={
            "tokens_used": tokens_used,
            "finish_reason": finish_reason,
            "response_length": len(text),
        })
        return LLMResponse(text=text, tokens_used=tokens_used, provider=f"lmstudio:{self._model}")

    async def _ollama_generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """POST /api/generate (Ollama format fallback)."""
        payload = {
            "model": self._model,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1024},
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{self._base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = data.get("response", "").strip()
        tokens_used = data.get("eval_count", 0) or 0
        logger.info("Ollama generation complete", extra={"tokens_used": tokens_used})
        return LLMResponse(text=text, tokens_used=tokens_used, provider=f"ollama:{self._model}")
