import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.models.conversation import Conversation, ConversationMessage, OrchestrationRun, OrchestrationStep


class ConversationService:
    """Service managing multi-turn conversation memory, messages, and execution run logs."""

    async def create_conversation(
        self,
        db: AsyncSession,
        title: Optional[str] = None,
        metadata_: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        conv = Conversation(
            id=str(uuid.uuid4()),
            title=title or "Satellite Conversation",
            metadata_=metadata_ or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        logger.info("Created conversation %s", conv.id)
        return conv

    async def get_conversation(self, conversation_id: str, db: AsyncSession) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_conversations(self, db: AsyncSession, limit: int = 50, offset: int = 0) -> List[Conversation]:
        stmt = select(Conversation).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_recent_messages(
        self,
        conversation_id: str,
        db: AsyncSession,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        max_limit = limit or settings.MAX_CONVERSATION_MESSAGES
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(max_limit)
        )
        res = await db.execute(stmt)
        messages = list(res.scalars().all())
        messages.reverse()  # chronological order
        return messages

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        db: AsyncSession,
        imagery_ids: Optional[List[str]] = None,
        task: Optional[str] = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            imagery_ids=imagery_ids or [],
            task=task,
            created_at=datetime.now(timezone.utc)
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def record_orchestration_run(
        self,
        db: AsyncSession,
        request_id: str,
        task: str,
        model: str,
        provider: str,
        status: str,
        duration_ms: float,
        fallback_used: bool,
        steps: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        errors: Optional[List[str]] = None,
        result_path: Optional[str] = None
    ) -> OrchestrationRun:
        run = OrchestrationRun(
            id=str(uuid.uuid4()),
            request_id=request_id,
            conversation_id=conversation_id,
            task=task,
            model=model,
            provider=provider,
            status=status,
            duration_ms=duration_ms,
            fallback_used=fallback_used,
            errors=errors,
            result_path=result_path,
            created_at=datetime.now(timezone.utc)
        )
        db.add(run)
        await db.flush()

        for idx, s in enumerate(steps):
            step_record = OrchestrationStep(
                id=str(uuid.uuid4()),
                run_id=run.id,
                step_number=s.get("step", idx + 1),
                stage=s.get("stage", "unknown"),
                action=s.get("action", s.get("stage", "action")),
                status=s.get("status", "completed"),
                duration_ms=float(s.get("duration_ms", 0.0)),
                created_at=datetime.now(timezone.utc)
            )
            db.add(step_record)

        await db.commit()
        return run


conversation_service = ConversationService()
