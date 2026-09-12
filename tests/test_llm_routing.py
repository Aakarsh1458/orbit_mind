from typing import AsyncIterator, List
from unittest.mock import AsyncMock, patch
import pytest
from pydantic import BaseModel, Field

from app.core.config import settings
from app.llm.base import (
    BaseLLMClient,
    LLMConfigurationError,
    LLMExecutionError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
    LLMSchemaValidationError,
)
from app.llm.gemini_client import GeminiClient
from app.llm.openrouter_client import OpenRouterClient
from app.llm.router import (
    CircuitBreaker,
    LLMRouter,
    WorkloadStage,
    circuit_breaker,
    llm_router,
)


class SampleSchema(BaseModel):
    intent: str = "URBAN_EXPANSION"
    confidence: float = 0.95
    satellite_sensor: str = "Sentinel-2"


@pytest.fixture(autouse=True)
def setup_api_keys(monkeypatch):
    """Ensure API keys are recognized as configured so mock routing executes through the failover decorator."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    circuit_breaker._failure_counts.clear()
    circuit_breaker._last_failure_time.clear()


@pytest.mark.asyncio
async def test_client_interface_conformance():
    """Verify that GeminiClient and OpenRouterClient adhere to the BaseLLMClient interface."""
    gemini = GeminiClient()
    openrouter = OpenRouterClient()

    assert isinstance(gemini, BaseLLMClient)
    assert isinstance(openrouter, BaseLLMClient)
    assert hasattr(gemini, "generate_chat")
    assert hasattr(gemini, "generate_structured")
    assert hasattr(gemini, "stream_chat")
    assert hasattr(gemini, "health_check")
    assert hasattr(openrouter, "generate_chat")
    assert hasattr(openrouter, "generate_structured")
    assert hasattr(openrouter, "stream_chat")
    assert hasattr(openrouter, "health_check")


@pytest.mark.asyncio
async def test_multi_model_stage_tiering_definitions():
    """Verify workload stage specialization and default tiering configurations."""
    # Stage 1: Query Understanding & Schema Extraction
    primary1, fallback1 = llm_router.get_stage_tiering(WorkloadStage.STAGE_1_QUERY_UNDERSTANDING)
    assert primary1["provider"] == "gemini"
    assert "gemini" in primary1["model"]
    assert fallback1["provider"] == "openrouter"
    assert "llama" in fallback1["model"]

    # Stage 2: Complex Task Planning & Spatial Disambiguation
    primary2, fallback2 = llm_router.get_stage_tiering(WorkloadStage.STAGE_2_TASK_PLANNING)
    assert primary2["provider"] == "openrouter"
    assert "claude" in primary2["model"]
    assert fallback2["provider"] == "gemini"
    assert "gemini" in fallback2["model"]

    # Stage 5: Vision Question Answering & Scene Reasoning
    primary5, fallback5 = llm_router.get_stage_tiering(WorkloadStage.STAGE_5_VQA)
    assert primary5["provider"] == "gemini"
    assert "gemini" in primary5["model"]
    assert fallback5["provider"] == "openrouter"
    assert "gpt-4o" in fallback5["model"]

    # Stage 8: Evidence-Grounded Response Generation
    primary8, fallback8 = llm_router.get_stage_tiering(WorkloadStage.STAGE_8_RESPONSE_GENERATION)
    assert primary8["provider"] == "gemini"
    assert "gemini" in primary8["model"]
    assert fallback8["provider"] == "openrouter"
    assert "deepseek" in fallback8["model"]


@pytest.mark.asyncio
async def test_simulated_gemini_429_triggers_openrouter_fallback():
    """
    Test Requirement:
    Mock network failures to verify that a simulated Gemini 429 rate limit error
    seamlessly triggers the OpenRouter fallback without breaking the response.
    """
    messages = [{"role": "user", "content": "Where did urban expansion occur?"}]

    with patch.object(
        llm_router._gemini,
        "generate_chat",
        new=AsyncMock(side_effect=LLMRateLimitError("gemini", "Simulated 429 Quota Exceeded"))
    ), patch.object(
        llm_router._openrouter,
        "generate_chat",
        new=AsyncMock(return_value="Urban expansion of 14.2 sq km observed in western quadrant.")
    ):
        result = await llm_router.route_chat(
            stage=WorkloadStage.STAGE_1_QUERY_UNDERSTANDING,
            messages=messages,
            temperature=0.2,
        )

        assert result["fallback_used"] is True
        assert result["provider_used"] == "openrouter"
        assert "14.2 sq km" in result["content"]


@pytest.mark.asyncio
async def test_simulated_gemini_timeout_triggers_openrouter_fallback():
    """Verify that a simulated Gemini timeout (408) triggers OpenRouter fallback."""
    messages = [{"role": "user", "content": "Analyze deforestation rates."}]

    with patch.object(
        llm_router._gemini,
        "generate_chat",
        new=AsyncMock(side_effect=LLMTimeoutError("gemini", "Request timed out after 120s"))
    ), patch.object(
        llm_router._openrouter,
        "generate_chat",
        new=AsyncMock(return_value="Deforestation rate estimated at 3.1% annually.")
    ):
        result = await llm_router.route_chat(
            stage=WorkloadStage.STAGE_8_RESPONSE_GENERATION,
            messages=messages,
        )

        assert result["fallback_used"] is True
        assert result["provider_used"] == "openrouter"
        assert "3.1%" in result["content"]


@pytest.mark.asyncio
async def test_simulated_gemini_503_service_unavailable_triggers_fallback():
    """Verify that a simulated 503 (service unavailable / overloaded) triggers fallback."""
    messages = [{"role": "user", "content": "Perform multi-temporal scene analysis."}]

    with patch.object(
        llm_router._gemini,
        "generate_chat",
        new=AsyncMock(side_effect=LLMServiceUnavailableError("gemini", "Model overloaded (503)"))
    ), patch.object(
        llm_router._openrouter,
        "generate_chat",
        new=AsyncMock(return_value="Multi-temporal radar coherence verified.")
    ):
        result = await llm_router.route_chat(
            stage=WorkloadStage.STAGE_5_VQA,
            messages=messages,
        )

        assert result["fallback_used"] is True
        assert result["provider_used"] == "openrouter"
        assert "radar coherence" in result["content"]


@pytest.mark.asyncio
async def test_structured_output_failover_on_schema_error():
    """Verify that structured output schema validation errors trigger fallback model."""
    messages = [{"role": "user", "content": "Extract remote sensing metadata."}]
    fallback_model_instance = SampleSchema(intent="WATER_DETECTION", confidence=0.98, satellite_sensor="Sentinel-1")

    with patch.object(
        llm_router._gemini,
        "generate_structured",
        new=AsyncMock(side_effect=LLMSchemaValidationError("gemini", "Malformed JSON returned by model"))
    ), patch.object(
        llm_router._openrouter,
        "generate_structured",
        new=AsyncMock(return_value=fallback_model_instance)
    ):
        res = await llm_router.route_structured(
            stage=WorkloadStage.STAGE_1_QUERY_UNDERSTANDING,
            messages=messages,
            response_model=SampleSchema,
        )

        assert res["fallback_used"] is True
        assert res["provider_used"] == "openrouter"
        assert res["parsed"].intent == "WATER_DETECTION"
        assert res["parsed"].satellite_sensor == "Sentinel-1"


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_fast_fails():
    """Verify circuit breaker opens after consecutive failures and fast-fails without hitting failing provider."""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout_seconds=60)
    key = "gemini:gemini-1.5-flash"

    assert not cb.is_open(key)
    cb.record_failure(key)
    assert not cb.is_open(key)
    cb.record_failure(key)
    assert not cb.is_open(key)
    cb.record_failure(key)
    # Threshold met -> circuit is open
    assert cb.is_open(key)

    # Success resets breaker
    cb.record_success(key)
    assert not cb.is_open(key)


@pytest.mark.asyncio
async def test_streaming_chat_yields_sequential_chunks():
    """Verify stream_chat yields SSE-ready chunks from LLM."""
    messages = [{"role": "user", "content": "Stream satellite summary."}]

    async def mock_stream_chunks(*args, **kwargs):
        for chunk in ["OrbitMind ", "detected ", "urban ", "growth."]:
            yield chunk

    with patch.object(llm_router._gemini, "is_configured", return_value=True), \
         patch.object(llm_router._gemini, "stream_chat", side_effect=mock_stream_chunks):
        chunks: List[str] = []
        async for chunk in llm_router.route_stream(WorkloadStage.STAGE_8_RESPONSE_GENERATION, messages):
            chunks.append(chunk)

        assert "".join(chunks) == "OrbitMind detected urban growth."
