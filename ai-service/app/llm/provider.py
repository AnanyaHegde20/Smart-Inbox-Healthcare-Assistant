"""LLM provider abstraction.

Supports multiple LLM backends through a common interface.
All providers must support structured JSON responses.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str = ""
    structured_data: dict[str, Any] | None = None
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""

    provider: str = "mock"
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout_seconds: int = 30


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction.
            response_format: "json" for structured JSON output.

        Returns:
            LLMResponse with content and optional structured_data.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        ...
