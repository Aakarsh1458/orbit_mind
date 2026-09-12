import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.ai.cloud_removal import CloudRemovalModel
from app.services.sen12mscr_service import sen12mscr_service, OrbitMindsDataset
from app.orchestration.orchestrator import orchestrator


@pytest.mark.asyncio
async def test_cloud_removal_model_mock():
    model = CloudRemovalModel(mode="mock")
    assert model.is_loaded
    caps = model.get_capabilities()
    assert "cloud_removal" in caps.tasks
    assert caps.min_inputs == 1


@pytest.mark.asyncio
async def test_sen12mscr_dataset_structure():
    ds = OrbitMindsDataset(split="train")
    assert len(ds) > 0
    sample = ds[0]
    assert "sar" in sample
    assert "optical" in sample
    assert "target" in sample
    assert sample["sar"].shape == (256, 256, 2)
    assert sample["optical"].shape == (256, 256, 13)
    assert sample["target"].shape == (256, 256, 13)


@pytest.mark.asyncio
async def test_dataset_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test listing samples
        res = await ac.get("/api/v1/dataset/samples?limit=3")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3
        assert data[0]["sample_idx"] == 0
        assert data[0]["modality"] == "Multimodal (Optical Sentinel-2 + SAR Sentinel-1)"

        # Test loading sample
        load_res = await ac.post("/api/v1/dataset/load-sample/0")
        assert load_res.status_code == 200
        load_data = load_res.json()
        assert "optical_imagery_id" in load_data
        assert "sar_imagery_id" in load_data
        assert len(load_data["imagery_ids"]) == 3


@pytest.mark.asyncio
async def test_comprehensive_6_models_orchestration():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Load sample to have valid raster IDs
        load_res = await ac.post("/api/v1/dataset/load-sample/0")
        assert load_res.status_code == 200
        ids = load_res.json()["imagery_ids"][:2]

        # Execute 6-model comprehensive query
        chat_res = await ac.post("/api/v1/chat", json={
            "message": "Perform all 6 remote sensing models: segmentation, change detection, captioning, vqa, optical-sar fusion, and cloud removal on this imagery",
            "imagery_ids": ids
        })
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert chat_data["status"] == "completed"
        assert chat_data["analysis"]["task"] == "comprehensive_analysis"
        assert len(chat_data["follow_up_suggestions"]) > 0
        assert len(chat_data["evidence"]) >= 5
