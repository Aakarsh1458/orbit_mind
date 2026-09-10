import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import query_service
from app.services.imagery_service import imagery_service

router = APIRouter(prefix="/api/v1/query", tags=["Query Understanding"])


@router.post(
    "",
    response_model=QueryResponse,
    summary="Understand natural language query",
    description="Analyzes a natural language remote-sensing query, identifies user intent, validates referenced imagery, and returns the selected analysis pipeline."
)
async def process_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    # Validate imagery existence
    for img_id in request.imagery_ids:
        record = await imagery_service.get_imagery_by_id(img_id, db)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referenced imagery_id '{img_id}' not found."
            )

    understanding = query_service.understand_query(request.query)

    return QueryResponse(
        query_id=str(uuid.uuid4()),
        query=request.query,
        detected_intent=understanding["intent"],
        confidence=understanding["confidence"],
        reason=understanding["reason"],
        selected_analysis=understanding["selected_analysis"],
        status="ready"
    )
