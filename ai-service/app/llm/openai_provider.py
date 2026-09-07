"""OpenAI LLM provider implementation.

Supports GPT-4, GPT-4o, and GPT-3.5-turbo models.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from .provider import LLMConfig, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: LLMConfig | None = None):
        if config is None:
            config = LLMConfig(
                provider="openai",
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
                timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            )
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(
                    base_url=self.config.base_url,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.config.timeout_seconds,
                )
            except ImportError:
                logger.error("httpx not installed. Run: pip install httpx")
                raise
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        start = time.perf_counter()

        if not self.config.api_key:
            return LLMResponse(
                content="",
                success=False,
                error="OPENAI_API_KEY not configured",
                model=self.config.model,
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if response_format == "json":
            body["response_format"] = {"type": "json_object"}

        try:
            client = self._get_client()
            response = client.post("/chat/completions", json=body)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            model = data.get("model", self.config.model)

            structured = None
            if response_format == "json":
                try:
                    structured = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM JSON response")

            latency = (time.perf_counter() - start) * 1000

            return LLMResponse(
                content=content,
                structured_data=structured,
                model=model,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
                latency_ms=round(latency, 2),
                success=True,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error("OpenAI API error: %s", e)
            return LLMResponse(
                content="",
                success=False,
                error=str(e),
                model=self.config.model,
                latency_ms=round(latency, 2),
            )

    def is_available(self) -> bool:
        return bool(self.config.api_key)

    def get_provider_name(self) -> str:
        return "openai"
