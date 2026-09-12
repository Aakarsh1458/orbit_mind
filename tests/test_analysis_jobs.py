from pathlib import Path
import pytest
from httpx import AsyncClient
from app.workers.analysis_worker import run_analysis_worker


@pytest.mark.asyncio
async def test_full_analysis_workflow(
    client: AsyncClient,
    sample_geotiff_t1: str,
    sample_geotiff_t2: str
):
    """
    End-to-end integration test executing the complete OrbitMind workflow:
    1. Upload 2022 and 2025 GeoTIFFs
    2. Query: "Where did urban expansion occur between 2022 and 2025?"
    3. Start analysis job -> queued
    4. Execute worker
    5. Monitor job -> completed
    6. Retrieve structured results, evidence, statistics, and execution trace
    7. Download generated change mask GeoTIFF
    """

    # 1. Upload 2022 Image
    with open(sample_geotiff_t1, "rb") as f:
        res1 = await client.post(
            "/api/v1/imagery/upload",
            files={"file": ("berlin_2022.tif", f.read(), "image/tiff")},
            data={"sensor": "Sentinel-2"}
        )
    assert res1.status_code == 201
    img1_id = res1.json()["id"]

    # 2. Upload 2025 Image
    with open(sample_geotiff_t2, "rb") as f:
        res2 = await client.post(
            "/api/v1/imagery/upload",
            files={"file": ("berlin_2025.tif", f.read(), "image/tiff")},
            data={"sensor": "Sentinel-2"}
        )
    assert res2.status_code == 201
    img2_id = res2.json()["id"]

    # 3. Post Query / Analysis Job
    analysis_payload = {
        "query": "Where did urban expansion occur between 2022 and 2025?",
        "imagery_ids": [img1_id, img2_id]
    }
    analysis_res = await client.post("/api/v1/analysis", json=analysis_payload)
    assert analysis_res.status_code == 202
    job_data = analysis_res.json()
    job_id = job_data["job_id"]
    assert job_data["status"] == "queued"
    assert job_data["analysis_type"] == "change_detection"

    # 4. Trigger background analysis worker
    await run_analysis_worker(job_id)

    # 5. Check Job Status
    job_status_res = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_status_res.status_code == 200
    job_status = job_status_res.json()
    assert job_status["status"] == "completed"
    assert job_status["progress"] == 1.0
    assert job_status["error"] is None
    assert job_status["completed_at"] is not None

    # 6. Retrieve Results
    results_res = await client.get(f"/api/v1/results/{job_id}")
    assert results_res.status_code == 200
    result = results_res.json()

    assert result["job_id"] == job_id
    assert result["analysis_type"] == "change_detection"
    assert result["mode"] == "mock"
    assert "summary" in result
    assert result["confidence"] > 0.8
    assert "changed_area_km2" in result["statistics"]
    assert "evidence" in result
    assert "change_mask" in result["evidence"]
    assert result["execution_trace"] == [
        "query_understanding",
        "imagery_validation",
        "geospatial_preprocessing",
        "change_detection",
        "statistics",
        "evidence_generation"
    ]

    # 7. Download Evidence Mask
    mask_path = result["evidence"]["change_mask"]
    filename = Path(mask_path).name
    dl_res = await client.get(f"/api/v1/results/{job_id}/download/{filename}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0


@pytest.mark.asyncio
async def test_analysis_job_not_found(client: AsyncClient):
    """Test requesting status and results for nonexistent job."""
    res1 = await client.get("/api/v1/jobs/unknown-job-id")
    assert res1.status_code == 404

    res2 = await client.get("/api/v1/results/unknown-job-id")
    assert res2.status_code == 404


@pytest.mark.asyncio
async def test_download_path_traversal_blocked(client: AsyncClient):
    """Verify that path traversal attempts in artifact download are strictly rejected with 400."""
    res = await client.get("/api/v1/results/any-job/download/..%2F..%2Fetc%2Fpasswd")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_download_direct_result_artifact(client: AsyncClient, tmp_path: Path):
    """Verify that universal download resolves artifacts located directly in RESULT_DIR."""
    from app.core.config import settings
    res_dir = Path(settings.RESULT_DIR)
    res_dir.mkdir(parents=True, exist_ok=True)

    test_tif = res_dir / "test_universal_artifact.tif"
    test_tif.write_bytes(b"SimulatedGeoTIFFContent")

    dl_res = await client.get(f"/api/v1/results/chat_req_123/download/{test_tif.name}")
    assert dl_res.status_code == 200
    assert dl_res.content == b"SimulatedGeoTIFFContent"


@pytest.mark.asyncio
async def test_segmentation_analysis_job(client: AsyncClient, sample_geotiff_t1: str):
    """Verify background worker execution for semantic land cover segmentation."""
    # 1. Upload scene
    with open(sample_geotiff_t1, "rb") as f:
        upload_res = await client.post(
            "/api/v1/imagery/upload",
            files={"file": ("seg_scene.tif", f.read(), "image/tiff")},
            data={"sensor": "Sentinel-2"}
        )
    assert upload_res.status_code == 201
    img_id = upload_res.json()["id"]

    # 2. Dispatch segmentation job
    res = await client.post(
        "/api/v1/analysis",
        json={"imagery_ids": [img_id], "analysis_type": "segmentation"}
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # 3. Run worker
    await run_analysis_worker(job_id)

    # 4. Fetch result
    job_res = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.json()["status"] == "completed"

    result_res = await client.get(f"/api/v1/results/{job_id}")
    result = result_res.json()
    assert result["analysis_type"] == "segmentation"
    assert "classes" in result["statistics"]
    assert "total_area_hectares" in result["statistics"]


@pytest.mark.asyncio
async def test_analysis_worker_failure(client: AsyncClient, sample_geotiff_t1: str):
    """Verify that worker handles errors gracefully and marks job failed."""
    # 1. Upload 1 image
    with open(sample_geotiff_t1, "rb") as f:
        upload_res = await client.post(
            "/api/v1/imagery/upload",
            files={"file": ("single_scene.tif", f.read(), "image/tiff")},
            data={"sensor": "Sentinel-2"}
        )
    assert upload_res.status_code == 201
    img_id = upload_res.json()["id"]

    # 2. Dispatch change detection job with only 1 image (requires 2)
    res = await client.post(
        "/api/v1/analysis",
        json={"imagery_ids": [img_id], "analysis_type": "change_detection"}
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # 3. Run worker
    await run_analysis_worker(job_id)

    # 4. Verify status is failed
    job_res = await client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.json()["status"] == "failed"
    assert job_res.json()["error"] is not None
    assert "requires at least 2 imagery datasets" in job_res.json()["error"]
    assert job_res.json()["completed_at"] is not None



