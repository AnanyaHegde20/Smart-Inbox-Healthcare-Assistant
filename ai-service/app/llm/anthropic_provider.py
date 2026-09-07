"""Anthropic LLM provider implementation.

Supports Claude 3.5 Sonnet, Claude 3 Opus, and Claude 3 Haiku models.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from .provider import LLMConfig, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(self, config: LLMConfig | None = None):
        if config is None:
            config = LLMConfig(
                provider="anthropic",
                model=os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
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
                        "x-api-key": self.config.api_key,
                        "anthropic-version": "2023-06-01",
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
                error="ANTHROPIC_API_KEY not configured",
                model=self.config.model,
            )

        body: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            body["system"] = system_prompt

        if response_format == "json":
            body["system"] = (body.get("system", "") + "\nRespond ONLY with valid JSON.").strip()

        try:
            client = self._get_client()
            response = client.post("/v1/messages", json=body)
            response.raise_for_status()
            data = response.json()

            content = data["content"][0]["text"]
            usage = data.get("usage", {})

            structured = None
            if response_format == "json":
                try:
                    structured = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Anthropic JSON response")

            latency = (time.perf_counter() - start) * 1000

            return LLMResponse(
                content=content,
                structured_data=structured,
                model=data.get("model", self.config.model),
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                },
                latency_ms=round(latency, 2),
                success=True,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error("Anthropic API error: %s", e)
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
        return "anthropic"
