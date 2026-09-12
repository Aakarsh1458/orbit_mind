from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default="New Satellite Session", json_schema_extra={"example": "Urban Monitoring 2022-2025"})
    metadata_: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PostMessageRequest(BaseModel):
    role: str = Field(default="user", json_schema_extra={"example": "user"})
    content: str = Field(..., json_schema_extra={"example": "Show me urban expansion."})
    imagery_ids: Optional[List[str]] = Field(default_factory=list)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new conversation session")
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.create_conversation(
        db=db,
        title=request.title,
        metadata_=request.metadata_
    )
    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at
    }


@router.get("", summary="List all conversation sessions")
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    items = await conversation_service.list_conversations(db=db, limit=limit, offset=offset)
    return [
        {
            "conversation_id": c.id,
            "title": c.title,
            "metadata": c.metadata_,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        }
        for c in items
    ]


@router.get("/{conversation_id}", summary="Get conversation details")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.get_conversation(conversation_id, db=db)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")
    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at
    }


@router.get("/{conversation_id}/messages", summary="Get conversation message history")
async def get_messages(
    conversation_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.get_conversation(conversation_id, db=db)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")

    msgs = await conversation_service.get_recent_messages(conversation_id, db=db, limit=limit)
    return {
        "conversation_id": conversation_id,
        "total_messages": len(msgs),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "imagery_ids": m.imagery_ids,
                "task": m.task,
                "created_at": m.created_at
            }
            for m in msgs
        ]
    }


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED, summary="Append a message to conversation")
async def post_message(
    conversation_id: str,
    request: PostMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.get_conversation(conversation_id, db=db)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Conversation '{conversation_id}' not found.")

    msg = await conversation_service.add_message(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
        db=db,
        imagery_ids=request.imagery_ids
    )
    return {
        "message_id": msg.id,
        "conversation_id": conversation_id,
        "role": msg.role,
        "content": msg.content,
        "created_at": msg.created_at
    }
