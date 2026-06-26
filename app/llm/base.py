"""
Abstract base class for LLM providers.
All LLM clients must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    provider: str


class BaseLLMClient(ABC):

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """
        Send a prompt to the LLM and return the response.

        Args:
            prompt: The user prompt / context + question
            system_prompt: Optional system-level instruction

        Returns:
            LLMResponse with text and token count
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        ...
