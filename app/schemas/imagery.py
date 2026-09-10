from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImageryMetadata(BaseModel):
    width: int
    height: int
    bands: int
    dtype: str
    nodata: Optional[float] = None
    crs: str
    transform: List[float]
    bounds: Dict[str, float]
    resolution: List[float]
    is_georeferenced: bool
    driver: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class ImageryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique imagery UUID")
    filename: str
    path: str
    sensor: Optional[str] = Field(default="Unknown", json_schema_extra={"example": "Sentinel-2"})
    acquisition_time: Optional[datetime] = None
    crs: str
    width: int
    height: int
    bands: int
    bounds: Dict[str, float]
    resolution: List[float]
    dtype: str = "uint8"
    is_georeferenced: bool = True
    file_size_bytes: int
    created_at: datetime
    meta_info: Optional[Dict[str, Any]] = None


class ImageryListResponse(BaseModel):
    total: int
    items: List[ImageryResponse]
