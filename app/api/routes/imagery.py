from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_safe_path, SecurityException
from app.geospatial.raster import get_or_create_preview_file
from app.schemas.imagery import ImageryResponse, ImageryListResponse
from app.services.imagery_service import imagery_service

router = APIRouter(prefix="/api/v1/imagery", tags=["Imagery"])


@router.post(
    "/upload",
    response_model=ImageryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload satellite imagery",
    description="Accepts GeoTIFF, TIFF, or PNG/JPEG satellite imagery. Extracts spatial metadata (CRS, bounds, resolution, transform) and registers the imagery."
)
async def upload_imagery(
    file: UploadFile = File(..., description="Satellite raster image file (.tif, .tiff, .png, .jpg)"),
    sensor: Optional[str] = Form(default="Unknown", description="Sensor name, e.g., 'Sentinel-2', 'Landsat-8', 'Sentinel-1'"),
    db: AsyncSession = Depends(get_db)
):
    try:
        record = await imagery_service.save_and_register_imagery(
            file=file,
            db=db,
            sensor=sensor
        )
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process imagery upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process imagery upload: {str(e)}"
        )


@router.get(
    "",
    response_model=ImageryListResponse,
    summary="List uploaded satellite imagery",
    description="Returns a paginated list of all uploaded satellite imagery records."
)
async def list_imagery(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    items = await imagery_service.list_imagery(db=db, limit=limit, offset=offset)
    return ImageryListResponse(total=len(items), items=items)


@router.get(
    "/{imagery_id}",
    response_model=ImageryResponse,
    summary="Get imagery metadata",
    description="Retrieves spatial metadata and properties for a specific imagery record by UUID."
)
async def get_imagery(
    imagery_id: str,
    db: AsyncSession = Depends(get_db)
):
    record = await imagery_service.get_imagery_by_id(imagery_id=imagery_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Imagery with ID '{imagery_id}' not found."
        )
    return record


@router.get(
    "/{imagery_id}/preview",
    summary="Get web-compatible preview image",
    description="Returns a browser-renderable PNG preview of the satellite raster with percentile contrast stretch."
)
async def get_imagery_preview(
    imagery_id: str,
    db: AsyncSession = Depends(get_db)
):
    record = await imagery_service.get_imagery_by_id(imagery_id=imagery_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Imagery with ID '{imagery_id}' not found."
        )

    raster_path = Path(record.path).resolve()
    if not raster_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raster file for imagery '{imagery_id}' does not exist on disk."
        )

    try:
        preview_file = get_or_create_preview_file(raster_path)
        return FileResponse(
            path=str(preview_file),
            media_type="image/png",
            filename=f"{raster_path.stem}_preview.png"
        )
    except Exception as e:
        logger.error("Failed to generate preview for imagery %s: %s", imagery_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get(
    "/{imagery_id}/file",
    summary="Download or stream raw imagery file",
    description="Streams the raw raster image file (GeoTIFF, PNG, JPEG)."
)
async def get_imagery_file(
    imagery_id: str,
    db: AsyncSession = Depends(get_db)
):
    record = await imagery_service.get_imagery_by_id(imagery_id=imagery_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Imagery with ID '{imagery_id}' not found."
        )

    raster_path = Path(record.path).resolve()
    if not raster_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raster file for imagery '{imagery_id}' does not exist on disk."
        )

    allowed_dirs = [
        Path(settings.UPLOAD_DIR).resolve(),
        Path(settings.PROCESSED_DIR).resolve(),
        Path(settings.RESULT_DIR).resolve(),
    ]
    try:
        safe_path = validate_safe_path(raster_path, allowed_base_dirs=allowed_dirs)
    except SecurityException as sec_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(sec_err.detail)
        )

    media_type = "image/tiff" if safe_path.suffix in (".tif", ".tiff") else "application/octet-stream"
    return FileResponse(
        path=str(safe_path),
        filename=safe_path.name,
        media_type=media_type
    )

