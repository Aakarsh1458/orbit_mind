import io
from pathlib import Path
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_geotiff(client: AsyncClient, sample_geotiff_t1: str):
    """Test uploading a valid GeoTIFF file and verifying metadata extraction."""
    file_path = Path(sample_geotiff_t1)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    response = await client.post(
        "/api/v1/imagery/upload",
        files={"file": (file_path.name, file_bytes, "image/tiff")},
        data={"sensor": "Sentinel-2"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["sensor"] == "Sentinel-2"
    assert data["width"] == 64
    assert data["height"] == 64
    assert data["bands"] == 3
    assert "EPSG:4326" in data["crs"]
    assert "bounds" in data
    assert data["bounds"]["left"] < data["bounds"]["right"]
    assert data["is_georeferenced"] is True
    assert data["file_size_bytes"] > 0


@pytest.mark.asyncio
async def test_list_and_get_imagery(client: AsyncClient, sample_geotiff_t2: str):
    """Test listing imagery and fetching single imagery details."""
    file_path = Path(sample_geotiff_t2)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    upload_res = await client.post(
        "/api/v1/imagery/upload",
        files={"file": (file_path.name, file_bytes, "image/tiff")},
        data={"sensor": "Landsat-8"}
    )
    assert upload_res.status_code == 201
    created_id = upload_res.json()["id"]

    # List
    list_res = await client.get("/api/v1/imagery")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == created_id for item in list_data["items"])

    # Get by ID
    get_res = await client.get(f"/api/v1/imagery/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created_id
    assert get_res.json()["sensor"] == "Landsat-8"


@pytest.mark.asyncio
async def test_upload_invalid_file_extension(client: AsyncClient):
    """Test that unauthorized file types (.sh, .exe) are rejected."""
    fake_bytes = b"echo 'malicious script'"
    response = await client.post(
        "/api/v1/imagery/upload",
        files={"file": ("exploit.sh", fake_bytes, "text/x-shellscript")}
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_get_nonexistent_imagery(client: AsyncClient):
    """Test that retrieving an unknown imagery ID returns 404."""
    response = await client.get("/api/v1/imagery/nonexistent-uuid-000")
    assert response.status_code == 404
