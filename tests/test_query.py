from pathlib import Path
import pytest
from httpx import AsyncClient
from app.services.query_service import query_service


def test_query_understanding_classification():
    """Verify rule-based classification across all remote sensing tasks."""
    cases = [
        ("Where did urban expansion occur between 2022 and 2025?", "change_detection"),
        ("Detect forest loss over time", "change_detection"),
        ("Highlight all flooded regions and water bodies", "segmentation"),
        ("Segment the urban footprint and roads", "segmentation"),
        ("What objects are visible in this sector?", "vqa"),
        ("Is there a bridge over the river?", "vqa"),
        ("Describe this satellite image", "captioning"),
        ("Generate caption for the scene", "captioning"),
        ("Compare optical and SAR radar imagery for cloud penetration", "optical_sar"),
    ]

    for query_text, expected_intent in cases:
        result = query_service.understand_query(query_text)
        assert result["intent"] == expected_intent
        assert result["confidence"] > 0.70
        assert "reason" in result


@pytest.mark.asyncio
async def test_query_api_endpoint(client: AsyncClient, sample_geotiff_t1: str):
    """Test POST /api/v1/query endpoint with valid and invalid imagery."""
    # First upload an image to get a valid imagery ID
    with open(sample_geotiff_t1, "rb") as f:
        upload_res = await client.post(
            "/api/v1/imagery/upload",
            files={"file": ("query_test.tif", f.read(), "image/tiff")}
        )
    img_id = upload_res.json()["id"]

    # Valid query
    response = await client.post(
        "/api/v1/query",
        json={
            "query": "Where did urban expansion occur between 2022 and 2025?",
            "imagery_ids": [img_id]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_intent"] == "change_detection"
    assert data["selected_analysis"] == "change_detection"
    assert data["status"] == "ready"

    # Nonexistent imagery ID
    bad_res = await client.post(
        "/api/v1/query",
        json={
            "query": "Where did urban expansion occur?",
            "imagery_ids": ["invalid-uuid-12345"]
        }
    )
    assert bad_res.status_code == 404
