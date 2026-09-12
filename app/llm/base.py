import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class LLMConfigurationError(Exception):
    """Raised when an LLM provider is requested but lacks necessary API key or endpoint configuration."""
    def __init__(self, provider: str, message: str = "Missing API key or configuration."):
        self.provider = provider
        super().__init__(f"Provider '{provider}' configuration error: {message}")


class LLMExecutionError(Exception):
    """Raised when an external LLM request fails due to network, model, or provider errors."""
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"Provider '{provider}' execution failed (status={status_code}): {message}")


class LLMRateLimitError(LLMExecutionError):
    """Raised when an LLM provider returns 429 Too Many Requests."""
    def __init__(self, provider: str, message: str = "Rate limit exceeded (429)."):
        super().__init__(provider=provider, message=message, status_code=429)


class LLMServiceUnavailableError(LLMExecutionError):
    """Raised when an LLM provider returns 503 Service Unavailable / Model Overloaded."""
    def __init__(self, provider: str, message: str = "Service unavailable or overloaded (503)."):
        super().__init__(provider=provider, message=message, status_code=503)


class LLMTimeoutError(LLMExecutionError):
    """Raised when an LLM request exceeds configured timeout."""
    def __init__(self, provider: str, message: str = "Request timed out."):
        super().__init__(provider=provider, message=message, status_code=408)


class LLMSchemaValidationError(LLMExecutionError):
    """Raised when an LLM response fails strict Pydantic schema validation."""
    def __init__(self, provider: str, message: str = "Output failed schema validation."):
        super().__init__(provider=provider, message=message, status_code=422)


class BaseLLMClient(ABC):
    """
    Core abstract asynchronous client interface for multi-provider LLM integrations
    (Google Gemini, OpenRouter, OpenAI, etc.).
    """

    def __init__(self, name: str):
        self.name = name.lower().strip()

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the required credentials/URLs are configured in the environment."""
        pass

    async def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Asynchronously executes a chat completion and returns generated text."""
        # Delegates to legacy chat if overridden by legacy provider
        return await self.chat(messages, temperature=temperature, max_tokens=max_tokens)

    async def generate_structured(
        self,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.0,
    ) -> T:
        """Asynchronously generates output strictly validated against target Pydantic model."""
        # Delegates to legacy structured_output if overridden by legacy provider
        return await self.structured_output(messages, response_model, temperature=temperature)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Default streaming fallback yields the generated text in chunks."""
        full_text = await self.generate_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
        chunk_size = 32
        for i in range(0, len(full_text), chunk_size):
            yield full_text[i:i + chunk_size]

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Validates provider configuration and connectivity.
        Guarantees that sensitive credentials are never leaked.
        """
        pass

    # Backwards-compatible legacy hooks
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Legacy interface; calls generate_chat if not overridden."""
        return await self.generate_chat(messages, temperature=temperature, max_tokens=max_tokens)

    async def structured_output(
        self,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """Legacy interface; calls generate_structured if not overridden."""
        return await self.generate_structured(messages, response_model, temperature=temperature)


# Backward-compatibility alias
BaseLLMProvider = BaseLLMClient
