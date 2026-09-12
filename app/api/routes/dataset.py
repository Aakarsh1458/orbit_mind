from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.sen12mscr_service import sen12mscr_service

router = APIRouter(prefix="/api/v1/dataset", tags=["Benchmark Datasets"])


@router.get("/samples", summary="List available SEN12MS-CR dataset samples")
async def list_dataset_samples(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns metadata for the first N samples in the Hermanni/sen12mscr benchmark dataset."""
    try:
        return await sen12mscr_service.list_available_samples(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dataset samples: {str(e)}"
        )


@router.post("/load-sample/{sample_idx}", summary="Load SEN12MS-CR sample and register GeoTIFFs")
async def load_dataset_sample(
    sample_idx: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Downloads/streams the specified sample from Hermanni/sen12mscr,
    generates georeferenced GeoTIFF files for Optical, SAR, and Target,
    registers them in the database, and returns their imagery IDs.
    """
    try:
        return await sen12mscr_service.load_and_register_sample(sample_idx=sample_idx, db=db)
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample index {sample_idx} not found in dataset."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load and register dataset sample: {str(e)}"
        )
