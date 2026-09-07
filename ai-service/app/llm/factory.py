"""LLM provider factory.

Creates the appropriate provider based on environment configuration.
"""

from __future__ import annotations

import logging
import os

from .provider import LLMConfig, LLMProvider
from .mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider() -> LLMProvider:
    """Create an LLM provider based on environment variables.

    Environment variables:
        LLM_PROVIDER: "openai", "anthropic", or "mock" (default: "mock")
        OPENAI_API_KEY: API key for OpenAI
        ANTHROPIC_API_KEY: API key for Anthropic
        LLM_MODEL: Model name (provider-specific default if empty)
        LLM_TEMPERATURE: Sampling temperature (default: 0.3)
        LLM_MAX_TOKENS: Max tokens (default: 4096)
        LLM_TIMEOUT_SECONDS: Request timeout (default: 30)

    Returns:
        Configured LLMProvider instance.
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set; falling back to mock provider")
            return MockLLMProvider()
        try:
            from .openai_provider import OpenAIProvider
            return OpenAIProvider()
        except Exception as e:
            logger.error("Failed to create OpenAI provider: %s", e)
            return MockLLMProvider()

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set; falling back to mock provider")
            return MockLLMProvider()
        try:
            from .anthropic_provider import AnthropicProvider
            return AnthropicProvider()
        except Exception as e:
            logger.error("Failed to create Anthropic provider: %s", e)
            return MockLLMProvider()

    elif provider_name == "mock":
        return MockLLMProvider()

    else:
        logger.warning("Unknown LLM_PROVIDER '%s'; falling back to mock", provider_name)
        return MockLLMProvider()
