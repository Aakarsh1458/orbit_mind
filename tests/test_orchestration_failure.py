import pytest
from app.ai.base import BaseRemoteSensingModel
from app.ai.registry import model_registry
from app.orchestration.orchestrator import OrbitMindOrchestrator


class AlwaysFailingModel(BaseRemoteSensingModel):
    def load(self):
        self.is_loaded = True

    def validate_input(self, inputs):
        return True

    def predict(self, inputs):
        raise RuntimeError("Fatal unrecoverable model crash")

    def postprocess(self, raw_output, metadata):
        return raw_output

    def get_metadata(self):
        return {"name": "AlwaysFailingModel", "task": "change_detection"}

    def get_capabilities(self):
        from app.ai.base import ModelCapability
        return ModelCapability(tasks=["change_detection"])


@pytest.mark.asyncio
async def test_all_models_fail_loop_halts(sample_geotiff_t1: str, sample_geotiff_t2: str):
    """
    Verifies Section 46:
    When both primary and fallback models fail, the orchestrator MUST NOT
    enter an infinite loop. It must halt cleanly, record errors, and return status 'failed'.
    """
    orig_primary = model_registry._registry.get("change_detection")
    orig_fallback = model_registry._fallbacks.get("change_detection")

    # Replace both primary and fallback with failing models
    model_registry._registry["change_detection"] = AlwaysFailingModel
    model_registry._fallbacks["change_detection"] = AlwaysFailingModel

    try:
        orch = OrbitMindOrchestrator()
        state = await orch.run(
            user_query="Where did urban expansion occur between 2022 and 2025?",
            imagery_ids=[sample_geotiff_t1, sample_geotiff_t2]
        )

        assert state.status == "failed"
        assert state.retry_count > 0
        assert len(state.errors) > 0
        assert "Fatal unrecoverable model crash" in str(state.errors)
        assert len(state.execution_steps) <= 8
        assert "AI execution failed" in (state.final_response or "")
    finally:
        if orig_primary:
            model_registry._registry["change_detection"] = orig_primary
        if orig_fallback:
            model_registry._fallbacks["change_detection"] = orig_fallback
