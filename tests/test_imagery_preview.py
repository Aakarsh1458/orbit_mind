import pytest
from pathlib import Path
from httpx import AsyncClient
import numpy as np

from app.geospatial.raster import write_geotiff


@pytest.mark.asyncio
async def test_imagery_preview_geotiff(client: AsyncClient, sample_geotiff_t1: str):
    """Test generating a web-compatible PNG preview from an uploaded GeoTIFF."""
    file_path = Path(sample_geotiff_t1)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    upload_res = await client.post(
        "/api/v1/imagery/upload",
        files={"file": (file_path.name, file_bytes, "image/tiff")},
        data={"sensor": "Sentinel-2"}
    )
    assert upload_res.status_code == 201
    img_id = upload_res.json()["id"]

    # Request PNG preview
    preview_res = await client.get(f"/api/v1/imagery/{img_id}/preview")
    assert preview_res.status_code == 200
    assert "image/png" in preview_res.headers["content-type"]
    assert preview_res.content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.asyncio
async def test_imagery_preview_sar_2bands(client: AsyncClient, tmp_path: Path):
    """Test generating a preview for a 2-band SAR raster (e.g. VV + VH)."""
    sar_data = np.random.randn(2, 32, 32).astype(np.float32)
    sar_file = tmp_path / "test_sar.tif"
    write_geotiff(sar_file, sar_data, transform=[0.0001, 0, 10, 0, -0.0001, 20], crs="EPSG:4326")

    with open(sar_file, "rb") as f:
        file_bytes = f.read()

    upload_res = await client.post(
        "/api/v1/imagery/upload",
        files={"file": (sar_file.name, file_bytes, "image/tiff")},
        data={"sensor": "Sentinel-1 SAR"}
    )
    assert upload_res.status_code == 201
    img_id = upload_res.json()["id"]

    preview_res = await client.get(f"/api/v1/imagery/{img_id}/preview")
    assert preview_res.status_code == 200
    assert "image/png" in preview_res.headers["content-type"]
    assert preview_res.content.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.asyncio
async def test_imagery_file_stream(client: AsyncClient, sample_geotiff_t2: str):
    """Test streaming the raw imagery file."""
    file_path = Path(sample_geotiff_t2)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    upload_res = await client.post(
        "/api/v1/imagery/upload",
        files={"file": (file_path.name, file_bytes, "image/tiff")},
        data={"sensor": "Landsat-8"}
    )
    assert upload_res.status_code == 201
    img_id = upload_res.json()["id"]

    file_res = await client.get(f"/api/v1/imagery/{img_id}/file")
    assert file_res.status_code == 200
    assert len(file_res.content) == len(file_bytes)


@pytest.mark.asyncio
async def test_imagery_preview_not_found(client: AsyncClient):
    """Test 404 response for nonexistent imagery ID."""
    res = await client.get("/api/v1/imagery/00000000-0000-0000-0000-000000000000/preview")
    assert res.status_code == 404
