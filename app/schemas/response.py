from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    service: str = Field(default="orbitmind-backend", json_schema_extra={"example": "orbitmind-backend"})
    version: Optional[str] = Field(default="1.0.0", json_schema_extra={"example": "1.0.0"})
    ai_mode: Optional[str] = Field(default="mock", json_schema_extra={"example": "mock"})


class AnalysisResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str = Field(..., description="ID of the completed analysis job")
    analysis_type: str = Field(..., json_schema_extra={"example": "change_detection"})
    mode: str = Field(..., description="'mock' or 'production'", json_schema_extra={"example": "mock"})
    summary: str = Field(..., json_schema_extra={"example": "Urban expansion detected in the selected region."})
    confidence: float = Field(..., ge=0.0, le=1.0, json_schema_extra={"example": 0.89})
    statistics: Dict[str, Any] = Field(
        ...,
        json_schema_extra={"example": {"changed_area_km2": 12.4, "percentage_changed": 4.5}}
    )
    evidence: Dict[str, Any] = Field(
        ...,
        json_schema_extra={"example": {"change_mask": "/data/results/change_mask.tif", "source_images": ["img1.tif", "img2.tif"]}}
    )
    execution_trace: List[str] = Field(
        ...,
        json_schema_extra={"example": [
            "query_understanding",
            "imagery_validation",
            "geospatial_preprocessing",
            "change_detection",
            "statistics",
            "evidence_generation"
        ]}
    )
    created_at: Optional[datetime] = None
