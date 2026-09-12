import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.orchestration.policies import (
    AIExecutionFailedError,
    FallbackPolicy,
    RetryPolicy,
)
from app.orchestration.state import OrchestrationState


class RetryEngine:
    """
    Manages retry loops and automated fallback invocation for model inference.
    Prevents infinite retries and applies exponential backoff for transient failures.
    """

    async def execute_with_retry_and_fallback(
        self,
        state: OrchestrationState,
        inference_func: Callable[[bool], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        max_retries = settings.MAX_RETRIES

        # Attempt 1..N on Primary Model
        for attempt in range(max_retries + 1):
            try:
                result = await inference_func(False)  # use_fallback = False
                return result
            except Exception as exc:
                last_error = exc
                state.retry_count += 1
                state.errors.append(f"Primary model attempt {attempt + 1} failed: {str(exc)}")
                logger.warning("Primary inference failed (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)

                if attempt < max_retries and RetryPolicy.is_retryable(exc):
                    delay = RetryPolicy.calculate_backoff(attempt)
                    logger.info("Retrying after %.2fs backoff...", delay)
                    await asyncio.sleep(delay)
                else:
                    break

        # If primary exhausted, check Fallback Policy
        if FallbackPolicy.should_fallback(state.selected_task or "", last_error, state.fallback_used):
            logger.info("Triggering fallback model for task '%s'...", state.selected_task)
            state.add_step(
                stage="retry",
                action="Primary model failed. Triggering configured fallback model.",
                status="completed"
            )
            try:
                result = await inference_func(True)  # use_fallback = True
                return result
            except Exception as fallback_exc:
                state.errors.append(f"Fallback model failed: {str(fallback_exc)}")
                logger.error("Fallback model also failed: %s", fallback_exc)

        # Failure
        state.status = "failed"
        state.add_step(
            stage="retry",
            action=f"Exhausted all retries and fallback options. Error: {last_error}",
            status="failed"
        )
        raise AIExecutionFailedError(f"AI execution failed after retries and fallback: {last_error}") from last_error
