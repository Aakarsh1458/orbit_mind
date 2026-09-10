from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language question or analysis request about satellite imagery.",
        json_schema_extra={"example": "Where did urban expansion occur between 2022 and 2025?"}
    )
    imagery_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of uploaded imagery IDs to analyze.",
        json_schema_extra={"example": ["img_2022_urban", "img_2025_urban"]}
    )


class QueryResponse(BaseModel):
    query_id: str = Field(..., description="Unique query session identifier")
    query: str
    detected_intent: str = Field(
        ...,
        description="Classified intent: 'vqa', 'captioning', 'change_detection', 'segmentation', 'optical_sar', 'unknown'",
        json_schema_extra={"example": "change_detection"}
    )
    confidence: float = Field(..., json_schema_extra={"example": 0.92})
    reason: str = Field(..., json_schema_extra={"example": "The query requests temporal surface changes between multiple dates."})
    selected_analysis: str = Field(..., json_schema_extra={"example": "change_detection"})
    status: str = Field(default="ready", json_schema_extra={"example": "ready"})
