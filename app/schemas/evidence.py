from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceOutput(BaseModel):
    change_mask: Optional[str] = Field(default=None, description="Path to generated change mask GeoTIFF")
    segmentation_mask: Optional[str] = Field(default=None, description="Path to generated segmentation GeoTIFF")
    fused_raster: Optional[str] = Field(default=None, description="Path to fused Optical+SAR GeoTIFF composite")
    source_images: List[str] = Field(default_factory=list, description="List of source imagery filepaths")
    crs: Optional[str] = Field(default=None, description="Coordinate Reference System")
    detected_regions_count: Optional[int] = Field(default=None, description="Number of vectorized polygons extracted")
    sample_footprints: Optional[List[Dict[str, Any]]] = Field(default=None, description="GeoJSON polygon footprints")
    extra: Optional[Dict[str, Any]] = None
