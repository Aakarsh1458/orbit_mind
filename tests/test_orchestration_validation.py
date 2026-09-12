import pytest
from app.ai.base import BaseRemoteSensingModel
from app.ai.registry import model_registry
from app.orchestration.orchestrator import OrbitMindOrchestrator
from app.orchestration.validator import OutputValidator, OutputValidationError


class InvalidOutputModel(BaseRemoteSensingModel):
    """Simulates a model returning text or corrupted dictionary instead of valid mask file."""
    def load(self):
        self.is_loaded = True

    def validate_input(self, inputs):
        return True

    def predict(self, inputs):
        # Invalid: returns string message and invalid confidence instead of mask & statistics
        return {
            "summary": "This is invalid output text instead of a raster mask",
            "confidence": float("nan"),  # NaN confidence
            "evidence": {}  # Missing change_mask
        }

    def postprocess(self, raw_output, metadata):
        return raw_output

    def get_metadata(self):
        return {"name": "InvalidOutputModel", "task": "change_detection"}

    def get_capabilities(self):
        from app.ai.base import ModelCapability
        return ModelCapability(tasks=["change_detection"])


def test_validator_rejects_invalid_output():
    """Unit test for OutputValidator directly."""
    validator = OutputValidator()

    # 1. Non-dict output
    with pytest.raises(OutputValidationError):
        validator.validate_model_output("change_detection", "not a dict")

    # 2. NaN confidence
    with pytest.raises(OutputValidationError):
        validator.validate_model_output("change_detection", {"confidence": float("nan")})

    # 3. Missing change_mask in evidence
    with pytest.raises(OutputValidationError):
        validator.validate_model_output("change_detection", {"confidence": 0.9, "evidence": {}})


@pytest.mark.asyncio
async def test_orchestration_catches_invalid_model_output(sample_geotiff_t1: str, sample_geotiff_t2: str):
    """Integration test: orchestrator halts and fails safely when model produces invalid output."""
    orig_primary = model_registry._registry.get("change_detection")
    orig_fallback = model_registry._fallbacks.get("change_detection")

    model_registry._registry["change_detection"] = InvalidOutputModel
    model_registry._fallbacks["change_detection"] = InvalidOutputModel

    try:
        orch = OrbitMindOrchestrator()
        state = await orch.run(
            user_query="Where did urban expansion occur between 2022 and 2025?",
            imagery_ids=[sample_geotiff_t1, sample_geotiff_t2]
        )

        assert state.status == "failed"
        assert any("OutputValidationError" in err or "confidence" in err or "change_mask" in err for err in state.errors)
    finally:
        if orig_primary:
            model_registry._registry["change_detection"] = orig_primary
        if orig_fallback:
            model_registry._fallbacks["change_detection"] = orig_fallback
