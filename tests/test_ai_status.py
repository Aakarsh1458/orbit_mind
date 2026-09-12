import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_status_endpoints(client: AsyncClient):
    """
    Verifies Section 32, 33, 34:
    GET /api/v1/ai/status
    GET /api/v1/ai/models
    GET /api/v1/ai/providers
    POST /api/v1/ai/providers/{provider}/validate
    """
    # 1. AI Status
    res_status = await client.get("/api/v1/ai/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "ai_mode" in data
    assert "llm" in data
    assert "device" in data
    assert "specialist_models" in data
    assert data["specialist_models"]["change_detection"] in ("available", "ready")
    assert "api_key" not in str(data)

    # 2. AI Models
    res_models = await client.get("/api/v1/ai/models")
    assert res_models.status_code == 200
    models = res_models.json()
    assert len(models) >= 5
    tasks = [m["task"] for m in models]
    assert "change_detection" in tasks
    assert "vqa" in tasks
    assert "segmentation" in tasks

    # 3. AI Providers
    res_prov = await client.get("/api/v1/ai/providers")
    assert res_prov.status_code == 200
    providers = res_prov.json()
    prov_names = [p["provider"] for p in providers]
    assert "gemini" in prov_names
    assert "openai" in prov_names
    assert "huggingface" in prov_names
    assert "openrouter" in prov_names
    assert "nemotron" in prov_names

    # 4. Safe Provider Validation
    res_val = await client.post("/api/v1/ai/providers/gemini/validate")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["provider"] == "gemini"
    assert "configured" in val_data
    assert "api_key" not in str(val_data)

    res_val_nemo = await client.post("/api/v1/ai/providers/nemotron/validate")
    assert res_val_nemo.status_code == 200
    val_nemo = res_val_nemo.json()
    assert val_nemo["provider"] == "nemotron"
    assert "api_key" not in str(val_nemo)
