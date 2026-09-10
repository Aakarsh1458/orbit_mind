import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator
import numpy as np
import pytest
import pytest_asyncio
import rasterio
from rasterio.transform import from_origin
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set environment variables for testing before importing app
os.environ["APP_ENV"] = "test"
os.environ["AI_MODE"] = "mock"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_orbitmind.db"
os.environ["UPLOAD_DIR"] = "./data/test_uploads"
os.environ["PROCESSED_DIR"] = "./data/test_processed"
os.environ["RESULT_DIR"] = "./data/test_results"

from app.core.config import settings
from app.models.database import Base, get_db
from app.main import app

# Test SQLite async engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test_orbitmind.db",
    connect_args={"check_same_thread": False}
)
test_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """Create test tables and directories, clean up after session."""
    settings.ensure_directories()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Teardown
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass
    finally:
        await test_engine.dispose()

    # Clean test files
    for d in (settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.RESULT_DIR):
        p = Path(d)
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    if os.path.exists("./test_orbitmind.db"):
        try:
            os.remove("./test_orbitmind.db")
        except (PermissionError, OSError):
            pass


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(scope="session")
def sample_geotiff_t1(tmp_path_factory) -> str:
    """Generates a small valid GeoTIFF for time T1 (2022 baseline)."""
    temp_dir = tmp_path_factory.mktemp("geotiff_data")
    file_path = temp_dir / "sample_2022.tif"

    width, height = 64, 64
    transform = from_origin(13.4050, 52.5200, 0.0001, 0.0001)  # Berlin region
    crs = "EPSG:4326"

    # 3 bands (e.g. RGB / multispectral)
    data = np.zeros((3, height, width), dtype=np.uint8)
    data[0, :, :] = 80   # Red
    data[1, :, :] = 160  # Green (vegetation)
    data[2, :, :] = 90   # Blue

    with rasterio.open(
        str(file_path),
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype="uint8",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)

    return str(file_path)


@pytest.fixture(scope="session")
def sample_geotiff_t2(tmp_path_factory) -> str:
    """Generates a small valid GeoTIFF for time T2 (2025 expansion)."""
    temp_dir = tmp_path_factory.mktemp("geotiff_data")
    file_path = temp_dir / "sample_2025.tif"

    width, height = 64, 64
    transform = from_origin(13.4050, 52.5200, 0.0001, 0.0001)
    crs = "EPSG:4326"

    # 3 bands where center pixels have changed (urban concrete/buildings)
    data = np.zeros((3, height, width), dtype=np.uint8)
    data[0, :, :] = 80
    data[1, :, :] = 160
    data[2, :, :] = 90

    # Add urban expansion in center
    data[:, 20:44, 20:44] = 230

    with rasterio.open(
        str(file_path),
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype="uint8",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)

    return str(file_path)
