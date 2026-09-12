import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.logging import logger
from app.orchestration.orchestrator import orchestrator
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/api/v1/chat", tags=["Chat & Orchestration"])


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="Natural language user query about satellite imagery.",
        json_schema_extra={"example": "Where did urban expansion occur between 2022 and 2025?"}
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation UUID for multi-turn context retention.",
        json_schema_extra={"example": None}
    )
    imagery_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="List of satellite imagery IDs to analyze.",
        json_schema_extra={"example": ["image_2022", "image_2025"]}
    )


@router.post(
    "",
    summary="Send chat message to AI Orchestration Engine",
    description="Synchronous conversational endpoint. Interprets query intent, plans task, routes specialist models, executes geospatial tools, validates output, and returns grounded answer with evidence."
)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    conv_id = request.conversation_id

    # Create conversation if not specified
    if not conv_id:
        conv = await conversation_service.create_conversation(db=db, title=request.message[:40])
        conv_id = conv.id
    else:
        conv = await conversation_service.get_conversation(conv_id, db=db)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conv_id}' not found."
            )

    # Store user message
    await conversation_service.add_message(
        conversation_id=conv_id,
        role="user",
        content=request.message,
        db=db,
        imagery_ids=request.imagery_ids
    )

    # Run AI orchestrator
    state = await orchestrator.run(
        user_query=request.message,
        imagery_ids=request.imagery_ids or [],
        conversation_id=conv_id,
        db=db
    )

    return state.to_safe_dict()


@router.post(
    "/stream",
    summary="Stream AI Orchestration Execution Events (SSE)",
    description="Server-Sent Events streaming endpoint. Emits safe real-time execution status events (planning, model_selection, preprocessing, inference, validation, completed)."
)
async def chat_stream_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    conv_id = request.conversation_id
    if not conv_id:
        conv = await conversation_service.create_conversation(db=db, title=request.message[:40])
        conv_id = conv.id

    # Store user message
    await conversation_service.add_message(
        conversation_id=conv_id,
        role="user",
        content=request.message,
        db=db,
        imagery_ids=request.imagery_ids
    )

    async def sse_event_generator():
        async for event in orchestrator.run_stream(
            user_query=request.message,
            imagery_ids=request.imagery_ids or [],
            conversation_id=conv_id,
            db=db
        ):
            event_name = event.get("event", "message")
            data_str = json.dumps(event.get("data", {}))
            yield f"event: {event_name}\ndata: {data_str}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
