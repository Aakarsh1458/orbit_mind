import pytest
from app.orchestration.orchestrator import OrbitMindOrchestrator


@pytest.mark.asyncio
async def test_missing_input_handling_temporal_query(sample_geotiff_t1: str):
    """
    Verifies Section 40:
    When a temporal change detection query is issued with only 1 imagery input,
    the orchestrator MUST NOT run the model.
    It must return status='needs_input' and specify the required inputs.
    """
    orch = OrbitMindOrchestrator()
    state = await orch.run(
        user_query="Where did urban expansion occur between 2022 and 2025?",
        imagery_ids=[sample_geotiff_t1]  # Only 1 image provided!
    )

    assert state.status == "needs_input"
    assert "required" in (state.final_response or "").lower()
    assert state.model_results is None  # Model was NOT run
    assert len(state.required_inputs) == 2

    # Verify safe serialization
    safe_dict = state.to_safe_dict()
    assert safe_dict["status"] == "needs_input"
    assert safe_dict["answer"] is not None
