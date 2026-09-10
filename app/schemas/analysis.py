from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalysisRequest(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Natural language query describing desired analysis.",
        json_schema_extra={"example": "Where did urban expansion occur between 2022 and 2025?"}
    )
    imagery_ids: List[str] = Field(
        ...,
        min_length=1,
        description="IDs of satellite images to analyze.",
        json_schema_extra={"example": ["img_id_2022", "img_id_2025"]}
    )
    analysis_type: Optional[str] = Field(
        default=None,
        description="Explicit analysis type ('change_detection', 'segmentation', 'vqa', 'captioning', 'optical_sar'). If omitted, inferred via query understanding.",
        json_schema_extra={"example": "change_detection"}
    )


class AnalysisJobResponse(BaseModel):
    job_id: str = Field(..., description="Unique analysis job UUID")
    status: str = Field(..., json_schema_extra={"example": "queued"})
    analysis_type: Optional[str] = Field(default=None, json_schema_extra={"example": "change_detection"})
    created_at: datetime


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    query: Optional[str] = None
    analysis_type: str
    status: str = Field(..., description="queued, processing, completed, or failed", json_schema_extra={"example": "completed"})
    progress: float = Field(..., ge=0.0, le=1.0, json_schema_extra={"example": 1.0})
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
