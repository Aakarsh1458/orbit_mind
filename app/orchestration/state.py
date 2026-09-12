import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    step: int
    stage: str
    action: str
    status: str = "completed"  # pending, completed, failed, skipped
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrchestrationState(BaseModel):
    """
    Typed, fully serializable state object tracking the execution lifecycle
    of a user query through the OrbitMind orchestration engine.
    Does NOT store hidden internal reasoning or chain-of-thought.
    """
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    user_query: str

    detected_intent: Optional[str] = None
    intent_confidence: float = 0.0

    required_inputs: List[str] = Field(default_factory=list)
    available_inputs: List[str] = Field(default_factory=list)  # imagery_ids or paths

    selected_task: Optional[str] = None
    selected_model: Optional[str] = None
    fallback_model: Optional[str] = None
    fallback_used: bool = False
    provider_used: str = "internal"

    execution_steps: List[ExecutionStep] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    model_results: Optional[Dict[str, Any]] = None

    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None

    retry_count: int = 0
    errors: List[str] = Field(default_factory=list)

    follow_up_suggestions: List[str] = Field(default_factory=list)
    final_response: Optional[str] = None
    status: str = "initialized"  # initialized, planning, routing, preprocessing, inference, validation, completed, failed, needs_input
    start_time: float = Field(default_factory=time.perf_counter)
    total_duration_ms: float = 0.0

    def add_step(self, stage: str, action: str, status: str = "completed", duration_ms: float = 0.0) -> None:
        step_num = len(self.execution_steps) + 1
        self.execution_steps.append(
            ExecutionStep(
                step=step_num,
                stage=stage,
                action=action,
                status=status,
                duration_ms=round(duration_ms, 2)
            )
        )

    def finalize(self) -> None:
        self.total_duration_ms = round((time.perf_counter() - self.start_time) * 1000, 2)

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serializes state omitting any sensitive internal fields."""
        return {
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "status": self.status,
            "answer": self.final_response,
            "analysis": {
                "task": self.selected_task,
                "model": self.selected_model,
                "fallback_used": self.fallback_used,
                "provider": self.provider_used
            },
            "statistics": self.statistics,
            "evidence": self.evidence,
            "follow_up_suggestions": self.follow_up_suggestions,
            "execution": {
                "steps": len(self.execution_steps),
                "duration_ms": self.total_duration_ms,
                "trace": [s.stage for s in self.execution_steps]
            },
            "errors": self.errors if self.errors else None
        }
