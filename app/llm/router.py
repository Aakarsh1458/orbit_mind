import asyncio
from enum import Enum
import functools
import time
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import (
    BaseLLMClient,
    BaseLLMProvider,
    LLMConfigurationError,
    LLMExecutionError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
    LLMSchemaValidationError,
)
from app.llm.gemini_client import GeminiClient
from app.llm.openrouter_client import OpenRouterClient
from app.llm.openai_provider import OpenAIProvider
from app.llm.huggingface_provider import HuggingFaceProvider
from app.llm.local_provider import LocalLLMProvider

T = TypeVar("T", bound=BaseModel)


class WorkloadStage(str, Enum):
    """Execution stages requiring specialized LLM capabilities."""
    STAGE_1_QUERY_UNDERSTANDING = "query_understanding"
    STAGE_2_TASK_PLANNING = "task_planning"
    STAGE_5_VQA = "vqa"
    STAGE_8_RESPONSE_GENERATION = "response_generation"


class CircuitBreaker:
    """
    Lightweight circuit breaker for LLM providers and models.
    Prevents cascading latency spikes by temporarily short-circuiting failing providers.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}

    def is_open(self, key: str) -> bool:
        """Returns True if the circuit breaker is tripped (open) and not ready for probe."""
        failures = self._failure_counts.get(key, 0)
        if failures < self.failure_threshold:
            return False

        last_time = self._last_failure_time.get(key, 0.0)
        elapsed = time.time() - last_time
        if elapsed > self.reset_timeout_seconds:
            # Half-open state: allow single probe request
            return False
        return True

    def record_success(self, key: str) -> None:
        """Resets the circuit breaker upon a successful execution."""
        self._failure_counts[key] = 0
        self._last_failure_time.pop(key, None)

    def record_failure(self, key: str) -> None:
        """Increments consecutive failure count and records timestamp."""
        self._failure_counts[key] = self._failure_counts.get(key, 0) + 1
        self._last_failure_time[key] = time.time()
        if self._failure_counts[key] >= self.failure_threshold:
            logger.warning(
                "Circuit breaker tripped for '%s' (%d consecutive failures). Circuit OPEN for %ds.",
                key, self._failure_counts[key], self.reset_timeout_seconds
            )


circuit_breaker = CircuitBreaker(
    failure_threshold=settings.LLM_CIRCUIT_BREAKER_FAIL_THRESHOLD,
    reset_timeout_seconds=settings.LLM_CIRCUIT_BREAKER_RESET_SECONDS
)


def automatic_failover():
    """
    Decorator for automatic failover routing across primary and fallback models.
    Catches rate limits (429), service unavailability (503), timeouts, and validation errors.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: "LLMRouter", *args, **kwargs):
            clean_kwargs = dict(kwargs)
            if "stage" in clean_kwargs:
                stage = clean_kwargs.pop("stage")
                stage_args = args
            elif args:
                stage = args[0]
                stage_args = args[1:]
            else:
                raise ValueError("Stage must be provided as first argument or keyword 'stage'")

            primary_info, fallback_info = self.get_stage_tiering(stage)

            # Check if primary is circuit-broken
            primary_key = f"{primary_info['provider']}:{primary_info['model']}"
            fallback_key = f"{fallback_info['provider']}:{fallback_info['model']}"

            if circuit_breaker.is_open(primary_key):
                logger.warning(
                    "Primary provider '%s' circuit breaker is OPEN. Fast-failing to fallback '%s'.",
                    primary_key, fallback_key
                )
                return await self._execute_fallback(stage, fallback_info, func, *stage_args, **clean_kwargs)

            try:
                result = await func(self, stage, *stage_args, target_provider=primary_info["provider"], target_model=primary_info["model"], **clean_kwargs)
                circuit_breaker.record_success(primary_key)
                return result
            except (LLMRateLimitError, LLMServiceUnavailableError, LLMTimeoutError, LLMSchemaValidationError, LLMExecutionError, LLMConfigurationError) as exc:
                circuit_breaker.record_failure(primary_key)
                logger.warning(
                    "Primary LLM %s failed for stage '%s': %s. Triggering fallback %s...",
                    primary_key, stage.value, exc, fallback_key
                )
                if not settings.ENABLE_FALLBACK:
                    raise

                return await self._execute_fallback(stage, fallback_info, func, *stage_args, **clean_kwargs)

        return wrapper
    return decorator


class LLMRouter:
    """
    Enterprise Multi-Provider LLM Router with Task-Specialized Tiering and Automated Failover.
    Coordinates Google AI Studio (Gemini) and OpenRouter (Claude 3.5 Sonnet, GPT-4o, DeepSeek, Llama 3.3).
    """

    def __init__(self):
        self._gemini = GeminiClient()
        self._openrouter = OpenRouterClient(name="openrouter")
        self._nemotron = OpenRouterClient(name="nemotron")
        self._openai = OpenAIProvider()
        self._huggingface = HuggingFaceProvider()
        self._local = LocalLLMProvider()

        self._providers: Dict[str, BaseLLMClient] = {
            "gemini": self._gemini,
            "openrouter": self._openrouter,
            "nemotron": self._nemotron,
            "openai": self._openai,
            "huggingface": self._huggingface,
            "local": self._local,
        }

    def register_provider(self, name: str, provider: BaseLLMClient) -> None:
        self._providers[name.lower().strip()] = provider

    def get_provider(self, name: Optional[str] = None) -> BaseLLMClient:
        provider_name = (name or settings.DEFAULT_LLM_PROVIDER).lower().strip()
        if provider_name not in self._providers:
            raise KeyError(f"Unknown LLM provider: '{provider_name}'. Available: {list(self._providers.keys())}")
        return self._providers[provider_name]

    def list_providers(self) -> List[Dict[str, Any]]:
        results = []
        for name, p in self._providers.items():
            results.append({
                "provider": name,
                "configured": p.is_configured(),
                "is_default": name == settings.DEFAULT_LLM_PROVIDER.lower().strip()
            })
        return results

    async def get_all_health(self) -> Dict[str, Any]:
        health_data = {}
        for name, provider in self._providers.items():
            health_data[name] = await provider.health_check()
        return health_data

    # =========================================================================
    # Task-Specialized Tiering Configuration
    # =========================================================================
    def get_stage_tiering(self, stage: WorkloadStage) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Returns (primary_config, fallback_config) for a given workload stage:
        - Stage 1 (QueryUnderstanding & Schema Extraction):
            Primary: gemini-1.5-flash
            Fallback: meta-llama/llama-3.3-70b-instruct
        - Stage 2 (Task Planning & Spatial Disambiguation):
            Primary: anthropic/claude-3.5-sonnet
            Fallback: gemini-1.5-pro
        - Stage 5 (Vision Question Answering / Geospatial Reasoning):
            Primary: gemini-1.5-pro
            Fallback: openai/gpt-4o
        - Stage 8 (Evidence-Grounded Response Generation):
            Primary: gemini-1.5-flash
            Fallback: deepseek/deepseek-chat
        """
        if stage == WorkloadStage.STAGE_1_QUERY_UNDERSTANDING:
            primary = {
                "provider": settings.LLM_STAGE_QUERY_UNDERSTANDING_PRIMARY_PROVIDER,
                "model": settings.LLM_STAGE_QUERY_UNDERSTANDING_PRIMARY_MODEL,
            }
            fallback = {
                "provider": settings.LLM_STAGE_QUERY_UNDERSTANDING_FALLBACK_PROVIDER,
                "model": settings.LLM_STAGE_QUERY_UNDERSTANDING_FALLBACK_MODEL,
            }
        elif stage == WorkloadStage.STAGE_2_TASK_PLANNING:
            primary = {
                "provider": settings.LLM_STAGE_TASK_PLANNING_PRIMARY_PROVIDER,
                "model": settings.LLM_STAGE_TASK_PLANNING_PRIMARY_MODEL,
            }
            fallback = {
                "provider": settings.LLM_STAGE_TASK_PLANNING_FALLBACK_PROVIDER,
                "model": settings.LLM_STAGE_TASK_PLANNING_FALLBACK_MODEL,
            }
        elif stage == WorkloadStage.STAGE_5_VQA:
            primary = {
                "provider": settings.LLM_STAGE_VQA_PRIMARY_PROVIDER,
                "model": settings.LLM_STAGE_VQA_PRIMARY_MODEL,
            }
            fallback = {
                "provider": settings.LLM_STAGE_VQA_FALLBACK_PROVIDER,
                "model": settings.LLM_STAGE_VQA_FALLBACK_MODEL,
            }
        elif stage == WorkloadStage.STAGE_8_RESPONSE_GENERATION:
            primary = {
                "provider": settings.LLM_STAGE_RESPONSE_GENERATION_PRIMARY_PROVIDER,
                "model": settings.LLM_STAGE_RESPONSE_GENERATION_PRIMARY_MODEL,
            }
            fallback = {
                "provider": settings.LLM_STAGE_RESPONSE_GENERATION_FALLBACK_PROVIDER,
                "model": settings.LLM_STAGE_RESPONSE_GENERATION_FALLBACK_MODEL,
            }
        else:
            primary = {"provider": "gemini", "model": settings.GEMINI_MODEL}
            fallback = {"provider": "openrouter", "model": settings.OPENROUTER_MODEL}

        return primary, fallback

    async def _execute_fallback(
        self,
        stage: WorkloadStage,
        fallback_info: Dict[str, str],
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        fallback_provider = self.get_provider(fallback_info["provider"])
        fallback_key = f"{fallback_info['provider']}:{fallback_info['model']}"

        # In mock mode, if fallback is also unconfigured, return mock deterministic output
        if settings.AI_MODE == "mock" and not fallback_provider.is_configured():
            logger.info("AI_MODE=mock and fallback provider %s unconfigured. Providing deterministic mock output.", fallback_key)
            if "response_model" in kwargs:
                return {
                    "parsed": kwargs["response_model"](),
                    "provider_used": "mock",
                    "model_used": "mock-model",
                    "fallback_used": True,
                    "stage": stage.value,
                }
            return {
                "content": f"OrbitMind AI: Analysis completed successfully (mock mode fallback for {stage.value}).",
                "provider_used": "mock",
                "model_used": "mock-model",
                "fallback_used": True,
                "stage": stage.value,
            }

        try:
            result = await func(self, stage, *args, target_provider=fallback_info["provider"], target_model=fallback_info["model"], **kwargs)
            circuit_breaker.record_success(fallback_key)
            if isinstance(result, dict):
                result["fallback_used"] = True
            return result
        except Exception as fallback_exc:
            circuit_breaker.record_failure(fallback_key)
            logger.error("Fallback LLM %s also failed for stage '%s': %s", fallback_key, stage.value, fallback_exc)

            if settings.AI_MODE == "mock":
                if "response_model" in kwargs:
                    return {
                        "parsed": kwargs["response_model"](),
                        "provider_used": "mock",
                        "model_used": "mock-model",
                        "fallback_used": True,
                        "stage": stage.value,
                    }
                return {
                    "content": f"OrbitMind AI: Analysis completed successfully (ultimate mock fallback for {stage.value}).",
                    "provider_used": "mock",
                    "model_used": "mock-model",
                    "fallback_used": True,
                    "stage": stage.value,
                }

            raise LLMExecutionError(
                fallback_info["provider"],
                f"Both primary and fallback models failed for stage '{stage.value}': {fallback_exc}"
            ) from fallback_exc

    # =========================================================================
    # Stage-Aware Routing Methods
    # =========================================================================
    @automatic_failover()
    async def route_chat(
        self,
        stage: WorkloadStage,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        target_provider: Optional[str] = None,
        target_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Routes chat query based on the workload stage with automatic failover.
        """
        provider_name = target_provider or settings.DEFAULT_LLM_PROVIDER
        client = self.get_provider(provider_name)

        if settings.AI_MODE == "mock" and not client.is_configured():
            logger.info("AI_MODE=mock and %s not configured. Returning deterministic mock response.", provider_name)
            return {
                "content": f"OrbitMind AI: Analysis completed successfully (mock mode for {stage.value}).",
                "provider_used": "mock",
                "model_used": target_model or "mock-model",
                "fallback_used": False,
                "stage": stage.value,
            }

        content = await client.generate_chat(
            messages=messages,
            model=target_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "content": content,
            "provider_used": client.name,
            "model_used": target_model or getattr(client, "default_model", client.name),
            "fallback_used": False,
            "stage": stage.value,
        }

    @automatic_failover()
    async def route_structured(
        self,
        stage: WorkloadStage,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        temperature: float = 0.0,
        target_provider: Optional[str] = None,
        target_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Routes structured schema extraction with automatic failover and strict schema enforcement.
        """
        provider_name = target_provider or settings.DEFAULT_LLM_PROVIDER
        client = self.get_provider(provider_name)

        if settings.AI_MODE == "mock" and not client.is_configured():
            logger.info("AI_MODE=mock and %s not configured. Returning default Pydantic model.", provider_name)
            return {
                "parsed": response_model(),
                "provider_used": "mock",
                "model_used": target_model or "mock-model",
                "fallback_used": False,
                "stage": stage.value,
            }

        parsed = await client.generate_structured(
            messages=messages,
            response_model=response_model,
            model=target_model,
            temperature=temperature,
        )

        return {
            "parsed": parsed,
            "provider_used": client.name,
            "model_used": target_model or getattr(client, "default_model", client.name),
            "fallback_used": False,
            "stage": stage.value,
        }

    async def route_stream(
        self,
        stage: WorkloadStage,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """
        Streams generated tokens for a stage with immediate fallback if connection fails.
        """
        primary_info, fallback_info = self.get_stage_tiering(stage)
        primary_client = self.get_provider(primary_info["provider"])

        if primary_client.is_configured() and not circuit_breaker.is_open(f"{primary_info['provider']}:{primary_info['model']}"):
            try:
                async for chunk in primary_client.stream_chat(
                    messages=messages,
                    model=primary_info["model"],
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yield chunk
                return
            except Exception as exc:
                logger.warning("Streaming on primary %s failed: %s. Attempting fallback stream...", primary_info["provider"], exc)

        # Fallback stream
        fallback_client = self.get_provider(fallback_info["provider"])
        if fallback_client.is_configured():
            async for chunk in fallback_client.stream_chat(
                messages=messages,
                model=fallback_info["model"],
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
        else:
            # Yield deterministic fallback message if no streaming provider configured
            yield f"OrbitMind AI: Analysis completed successfully (streaming fallback for {stage.value})."

    # =========================================================================
    # Backwards-Compatible Generic Chat and Structured Output
    # =========================================================================
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        provider_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Backwards-compatible chat endpoint."""
        target = provider_name or settings.DEFAULT_LLM_PROVIDER
        primary = self.get_provider(target)

        if settings.AI_MODE == "mock" and not primary.is_configured():
            return {
                "content": "OrbitMind AI Assistant: Analysis of the satellite data completed successfully.",
                "provider_used": "mock",
                "fallback_used": False,
            }

        try:
            content = await primary.generate_chat(messages, temperature=temperature, max_tokens=max_tokens)
            return {
                "content": content,
                "provider_used": primary.name,
                "fallback_used": False,
            }
        except (LLMConfigurationError, LLMExecutionError) as err:
            logger.warning("Primary LLM provider %s failed: %s", primary.name, err)
            if not settings.ENABLE_FALLBACK:
                raise

            for alt_name, alt_provider in self._providers.items():
                if alt_name != primary.name and alt_provider.is_configured():
                    try:
                        content = await alt_provider.generate_chat(messages, temperature=temperature, max_tokens=max_tokens)
                        return {
                            "content": content,
                            "provider_used": alt_name,
                            "fallback_used": True,
                        }
                    except Exception as alt_err:
                        logger.warning("Fallback provider %s also failed: %s", alt_name, alt_err)

            if settings.AI_MODE == "mock":
                return {
                    "content": "OrbitMind AI Assistant: Analysis of satellite data completed successfully (mock fallback).",
                    "provider_used": "mock",
                    "fallback_used": True,
                }

            raise LLMExecutionError(primary.name, "All available LLM providers failed or are unconfigured.")

    async def structured_output(
        self,
        messages: List[Dict[str, Any]],
        response_model: Type[T],
        provider_name: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Backwards-compatible structured output endpoint."""
        target = provider_name or settings.DEFAULT_LLM_PROVIDER
        primary = self.get_provider(target)

        if settings.AI_MODE == "mock" and not primary.is_configured():
            return {
                "parsed": response_model(),
                "provider_used": "mock",
                "fallback_used": False,
            }

        try:
            parsed = await primary.generate_structured(messages, response_model, temperature=temperature)
            return {
                "parsed": parsed,
                "provider_used": primary.name,
                "fallback_used": False,
            }
        except (LLMConfigurationError, LLMExecutionError) as err:
            logger.warning("Primary structured LLM provider %s failed: %s", primary.name, err)
            if not settings.ENABLE_FALLBACK:
                raise

            for alt_name, alt_provider in self._providers.items():
                if alt_name != primary.name and alt_provider.is_configured():
                    try:
                        parsed = await alt_provider.generate_structured(messages, response_model, temperature=temperature)
                        return {
                            "parsed": parsed,
                            "provider_used": alt_name,
                            "fallback_used": True,
                        }
                    except Exception as alt_err:
                        logger.warning("Fallback structured provider %s failed: %s", alt_name, alt_err)

            if settings.AI_MODE == "mock":
                return {
                    "parsed": response_model(),
                    "provider_used": "mock",
                    "fallback_used": True,
                }

            raise LLMExecutionError(primary.name, "All available LLM providers failed to produce structured output.")


llm_router = LLMRouter()
