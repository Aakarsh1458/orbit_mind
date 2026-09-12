from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool: str = Field(..., description="The registered tool name to invoke.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary for the tool.")


class ToolResult(BaseModel):
    tool: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# Tool-specific argument validation models
class GetImageryMetadataArgs(BaseModel):
    file_path: str


class ReadRasterArgs(BaseModel):
    file_path: str
    bands: Optional[List[int]] = None


class ReprojectRasterArgs(BaseModel):
    src_path: str
    dst_path: str
    target_crs: str = "EPSG:4326"


class AlignRastersArgs(BaseModel):
    reference_path: str
    target_path: str
    output_path: str


class CalculateAreaArgs(BaseModel):
    geometry: Union[Dict[str, Any], Any]
    crs: str = "EPSG:4326"


class CalculateStatisticsArgs(BaseModel):
    change_mask_path: str
    pixel_res_x: float = 0.0001
    pixel_res_y: float = 0.0001
    crs: str = "EPSG:4326"


class CreateChangeMaskArgs(BaseModel):
    path_t1: str
    path_t2: str
    output_path: str


class CreateSegmentationMaskArgs(BaseModel):
    raster_path: str
    output_path: str


class PolygonizeMaskArgs(BaseModel):
    mask_path: str
    value_to_extract: int = 1


class SaveGeospatialResultArgs(BaseModel):
    data_type: str
    source_path: str
    destination_path: str


class ReadMetadataArgs(BaseModel):
    file_path: str


class ComputeGeodesicAreaArgs(BaseModel):
    geometry: Union[Dict[str, Any], Any]
    crs: str = "EPSG:4326"


class CalculateZonalStatsArgs(BaseModel):
    raster_path: str
    zones_path_or_geometry: Union[str, Dict[str, Any]]
    crs: str = "EPSG:4326"

