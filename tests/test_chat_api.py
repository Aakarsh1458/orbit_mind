from pathlib import Path
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_endpoint_sync(client: AsyncClient, sample_geotiff_t1: str, sample_geotiff_t2: str):
    """
    Verifies Section 7 & 49:
    POST /api/v1/chat executes full orchestration and returns safe structured JSON.
    """
    # 1. Upload two test scenes to get valid IDs
    with open(sample_geotiff_t1, "rb") as f1:
        res1 = await client.post("/api/v1/imagery/upload", files={"file": ("chat_2022.tif", f1.read(), "image/tiff")})
    id1 = res1.json()["id"]

    with open(sample_geotiff_t2, "rb") as f2:
        res2 = await client.post("/api/v1/imagery/upload", files={"file": ("chat_2025.tif", f2.read(), "image/tiff")})
    id2 = res2.json()["id"]

    # 2. Call /api/v1/chat
    payload = {
        "message": "Where did urban expansion occur between 2022 and 2025?",
        "imagery_ids": [id1, id2]
    }
    chat_res = await client.post("/api/v1/chat", json=payload)
    assert chat_res.status_code == 200
    data = chat_res.json()

    assert "request_id" in data
    assert "conversation_id" in data
    assert data["status"] == "completed"
    assert "answer" in data and len(data["answer"]) > 0
    assert data["analysis"]["task"] == "change_detection"
    assert "statistics" in data
    assert "evidence" in data
    assert "execution" in data
    assert data["execution"]["steps"] > 0
    assert "trace" in data["execution"]


@pytest.mark.asyncio
async def test_chat_endpoint_streaming(client: AsyncClient, sample_geotiff_t1: str, sample_geotiff_t2: str):
    """
    Verifies Section 8:
    POST /api/v1/chat/stream emits SSE execution events.
    """
    payload = {
        "message": "Where did urban expansion occur between 2022 and 2025?",
        "imagery_ids": [sample_geotiff_t1, sample_geotiff_t2]
    }

    response = await client.post("/api/v1/chat/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    body = response.text
    assert "event: status" in body
    assert "planning" in body
    assert "event: completed" in body or "event: failed" in body
