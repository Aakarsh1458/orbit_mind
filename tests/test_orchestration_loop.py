import pytest
from app.ai.base import BaseRemoteSensingModel
from app.ai.registry import model_registry
from app.orchestration.orchestrator import OrbitMindOrchestrator


class FailingPrimaryModel(BaseRemoteSensingModel):
    """Simulates a primary model that encounters a runtime failure."""
    def load(self):
        self.is_loaded = True

    def validate_input(self, inputs):
        return True

    def predict(self, inputs):
        raise RuntimeError("Transient CUDA hardware failure on primary model")

    def postprocess(self, raw_output, metadata):
        return raw_output

    def get_metadata(self):
        return {"name": "FailingPrimaryModel", "task": "change_detection"}

    def get_capabilities(self):
        from app.ai.base import ModelCapability
        return ModelCapability(tasks=["change_detection"])


@pytest.mark.asyncio
async def test_orchestration_retry_and_fallback_loop(sample_geotiff_t1: str, sample_geotiff_t2: str):
    """
    Verifies Section 45:
    User query -> Planner -> Router -> Primary model failure -> Retry -> Fallback model ->
    Successful inference -> Validation -> Evidence -> Response.
    Verifies that the loop terminates successfully and fallback_used is True.
    """
    # Temporarily register the failing primary model
    original_primary = model_registry._registry.get("change_detection")
    model_registry.register("change_detection", FailingPrimaryModel)

    try:
        orch = OrbitMindOrchestrator()
        state = await orch.run(
            user_query="Where did urban expansion occur between 2022 and 2025?",
            imagery_ids=[sample_geotiff_t1, sample_geotiff_t2]
        )

        assert state.status == "completed"
        assert state.fallback_used is True
        assert state.retry_count > 0
        assert len(state.errors) > 0
        assert "Transient CUDA hardware failure" in state.errors[0]
        assert state.final_response is not None
        assert len(state.evidence) > 0
        assert len(state.execution_steps) <= 12

        # Verify trace contains retry
        trace_stages = [s.stage for s in state.execution_steps]
        assert "retry" in trace_stages
        assert "evidence_generation" in trace_stages
    finally:
        # Restore original primary model
        if original_primary:
            model_registry._registry["change_detection"] = original_primary
