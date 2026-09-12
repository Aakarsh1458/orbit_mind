import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Satellite Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSON, nullable=True)

    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")
    runs = relationship("OrchestrationRun", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    imagery_ids = Column(JSON, nullable=True)  # list of referenced imagery IDs
    task = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


class OrchestrationRun(Base):
    __tablename__ = "orchestration_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    task = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False, default="internal")
    status = Column(String(20), nullable=False, default="completed")  # completed, failed, needs_input
    duration_ms = Column(Float, nullable=False, default=0.0)
    fallback_used = Column(Boolean, nullable=False, default=False)
    errors = Column(JSON, nullable=True)
    result_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="runs")
    steps = relationship("OrchestrationStep", back_populates="run", cascade="all, delete-orphan", order_by="OrchestrationStep.step_number")


class OrchestrationStep(Base):
    __tablename__ = "orchestration_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("orchestration_runs.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    stage = Column(String(50), nullable=False)
    action = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="completed")
    duration_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("OrchestrationRun", back_populates="steps")
