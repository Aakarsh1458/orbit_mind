import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size
from app.geospatial.raster import read_raster_metadata
from app.models.imagery import Imagery


class ImageryService:
    """Service managing satellite image uploads, metadata extraction, and storage."""

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_and_register_imagery(
        self,
        file: UploadFile,
        db: AsyncSession,
        sensor: Optional[str] = "Unknown"
    ) -> Imagery:
        # Validate filename and extension
        original_filename = file.filename or "imagery.tif"
        validate_file_extension(original_filename)

        safe_filename = sanitize_filename(original_filename)
        destination_path = self.upload_dir / safe_filename

        # Stream save file to disk
        file_size = 0
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                validate_file_size(file_size)
                buffer.write(chunk)

        logger.info("Saved uploaded file to %s (%d bytes)", destination_path, file_size)

        # Extract raster metadata via Rasterio / GDAL
        try:
            metadata = read_raster_metadata(destination_path)
        except Exception as e:
            # Clean up on failure
            if destination_path.exists():
                destination_path.unlink()
            logger.error("Failed to extract metadata from %s: %s", destination_path, e)
            raise ValueError(f"Could not extract geospatial metadata from uploaded file: {e}")

        imagery_record = Imagery(
            id=str(uuid.uuid4()),
            filename=original_filename,
            path=str(destination_path),
            sensor=sensor or "Unknown",
            crs=metadata["crs"],
            width=metadata["width"],
            height=metadata["height"],
            bands=metadata["bands"],
            bounds=metadata["bounds"],
            resolution=metadata["resolution"],
            dtype=metadata["dtype"],
            is_georeferenced=metadata.get("is_georeferenced", True),
            file_size_bytes=file_size,
            meta_info={
                "driver": metadata.get("driver"),
                "transform": metadata.get("transform"),
                "tags": metadata.get("tags")
            }
        )

        db.add(imagery_record)
        await db.commit()
        await db.refresh(imagery_record)

        logger.info("Successfully registered imagery record: %s", imagery_record.id)
        return imagery_record

    async def get_imagery_by_id(self, imagery_id: str, db: AsyncSession) -> Optional[Imagery]:
        stmt = select(Imagery).where(Imagery.id == imagery_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_imagery(self, db: AsyncSession, limit: int = 50, offset: int = 0) -> List[Imagery]:
        stmt = select(Imagery).order_by(Imagery.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())


imagery_service = ImageryService()
