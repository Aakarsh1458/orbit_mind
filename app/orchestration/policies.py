import asyncio
from typing import Any, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.llm.base import LLMExecutionError
from app.ai.base import ModelUnavailableError


class OrchestrationStalledError(Exception):
    """Raised when an agent stage repeats without advancing the execution state."""
    pass


class AIExecutionFailedError(Exception):
    """Raised when an orchestration loop exhausts maximum retries and fallbacks."""
    pass


class InsufficientSpatialOverlapError(Exception):
    """Raised when bitemporal satellite scenes have no valid spatial intersection."""
    pass


class RetryPolicy:
    """Classifies errors and calculates exponential backoff durations."""

    NON_RETRYABLE_EXCEPTIONS = (
        ValueError,
        KeyError,
        FileNotFoundError,
        InsufficientSpatialOverlapError,
        ModelUnavailableError,
    )

    @classmethod
    def is_retryable(cls, exc: Exception) -> bool:
        if isinstance(exc, cls.NON_RETRYABLE_EXCEPTIONS):
            return False

        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, LLMExecutionError)):
            return True

        # Check for CUDA OOM or transient network phrases in string
        err_msg = str(exc).lower()
        if any(w in err_msg for w in ["timeout", "connection reset", "temporarily unavailable", "rate limit", "503", "502"]):
            return True

        return False

    @classmethod
    def calculate_backoff(cls, attempt: int) -> float:
        """Returns backoff delay in seconds: attempt 0 -> 0.2s, attempt 1 -> 0.4s, attempt 2 -> 0.8s."""
        return min(2.0, 0.2 * (2 ** attempt))


class FallbackPolicy:
    """Determines when to activate alternate models or providers."""

    @classmethod
    def should_fallback(cls, task: str, error: Exception, fallback_used: bool) -> bool:
        if fallback_used or not settings.ENABLE_FALLBACK:
            return False
        # If it's a model failure, allow fallback
        return True


class SafetyPolicy:
    """Enforces execution step limits and loop stall protection."""

    @classmethod
    def check_loop_safety(cls, steps: List[Any], max_steps: Optional[int] = None) -> None:
        limit = max_steps or (settings.MAX_AGENT_STEPS + settings.MAX_RETRIES * 2)
        if len(steps) >= limit:
            raise OrchestrationStalledError(
                f"Agent step limit exceeded ({len(steps)}/{limit}). Halting to prevent infinite loop."
            )

        # Detect consecutive repeated stages without progress
        if len(steps) >= 4:
            last_4 = [s.stage for s in steps[-4:]]
            if len(set(last_4)) == 1:
                raise OrchestrationStalledError(
                    f"Agent stalled: stage '{last_4[0]}' repeated 4 times consecutively without progress."
                )
