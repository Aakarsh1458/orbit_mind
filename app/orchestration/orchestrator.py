import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.orchestration.executor import ExecutionEngine
from app.orchestration.planner import TaskPlanner
from app.orchestration.policies import (
    AIExecutionFailedError,
    InsufficientSpatialOverlapError,
    OrchestrationStalledError,
    SafetyPolicy,
)
from app.orchestration.response_generator import ResponseGenerator
from app.orchestration.retry_engine import RetryEngine
from app.orchestration.router import ModelRouter
from app.orchestration.state import OrchestrationState
from app.orchestration.validator import OutputValidator, OutputValidationError
from app.services.conversation_service import conversation_service
from app.services.imagery_service import imagery_service


class OrbitMindOrchestrator:
    """
    Primary AI orchestration controller for OrbitMind.
    Coordinates the natural language -> intent -> planning -> routing -> tool execution ->
    inference -> validation -> retry/fallback -> evidence -> response pipeline.
    Enforces loop boundaries and emits streaming execution events.
    """

    def __init__(self):
        self.planner = TaskPlanner()
        self.router = ModelRouter()
        self.executor = ExecutionEngine()
        self.validator = OutputValidator()
        self.retry_engine = RetryEngine()
        self.response_generator = ResponseGenerator()

    async def run(
        self,
        user_query: str,
        imagery_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> OrchestrationState:
        """Executes the full orchestration lifecycle synchronously and returns final state."""
        state = OrchestrationState(
            user_query=user_query,
            conversation_id=conversation_id,
            available_inputs=imagery_ids or []
        )

        async for _ in self._orchestration_generator(state, db):
            pass

        return state

    async def run_stream(
        self,
        user_query: str,
        imagery_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Executes orchestration and yields real-time execution status events for SSE."""
        state = OrchestrationState(
            user_query=user_query,
            conversation_id=conversation_id,
            available_inputs=imagery_ids or []
        )

        async for event in self._orchestration_generator(state, db):
            yield event

    async def _orchestration_generator(
        self,
        state: OrchestrationState,
        db: Optional[AsyncSession] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            # 0. Multi-turn context inheritance
            if not state.available_inputs and state.conversation_id and db:
                try:
                    recent = await conversation_service.get_recent_messages(state.conversation_id, db=db, limit=5)
                    for m in reversed(recent):
                        if m.imagery_ids:
                            state.available_inputs = list(m.imagery_ids)
                            state.add_step(
                                stage="context_inheritance",
                                action=f"Inherited {len(state.available_inputs)} imagery inputs from conversation history",
                                status="completed"
                            )
                            break
                except Exception as ctx_err:
                    logger.warning("Could not inherit conversation context: %s", ctx_err)

            # 1. Planning & Intent Understanding
            yield {"event": "status", "data": {"stage": "planning"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)
            await self.planner.understand_and_plan(state)

            if state.status == "needs_input":
                state.finalize()
                yield {"event": "needs_input", "data": state.to_safe_dict()}
                return

            # Resolve imagery paths from DB or inputs
            imagery_paths: List[str] = []
            if db:
                for img_id in state.available_inputs:
                    rec = await imagery_service.get_imagery_by_id(img_id, db)
                    if rec:
                        imagery_paths.append(rec.path)
            if not imagery_paths:
                imagery_paths = [p for p in state.available_inputs if Path(p).exists()]

            # 2. Model Routing
            yield {"event": "status", "data": {"stage": "model_selection"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)
            self.router.route_model(state)

            # 3. Geospatial Preprocessing & Input Validation
            yield {"event": "status", "data": {"stage": "preprocessing"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)
            self.validator.validate_geospatial_inputs(imagery_paths)
            prepared_paths = await self.executor.execute_preprocessing(state, imagery_paths)

            # 4. Model Inference with Retry & Fallback
            yield {"event": "status", "data": {"stage": "inference"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)

            async def _inference_call(use_fallback: bool) -> Dict[str, Any]:
                return await self.executor.execute_model_inference(state, prepared_paths, use_fallback=use_fallback)

            raw_model_output = await self.retry_engine.execute_with_retry_and_fallback(state, _inference_call)

            # 5. Output Validation
            yield {"event": "status", "data": {"stage": "validation"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)
            self.validator.validate_model_output(state.selected_task or "", raw_model_output)
            state.add_step(
                stage="validation",
                action="Model inference output successfully passed all schema and numerical checks",
                status="completed"
            )

            # 6. Extract Statistics and Evidence
            state.statistics = raw_model_output.get("statistics", {})
            evidence_dict = raw_model_output.get("evidence", {})
            evidence_items = []
            for k, v in evidence_dict.items():
                if isinstance(v, str):
                    evidence_items.append({"type": k, "path": v})
                elif isinstance(v, list) and v and isinstance(v[0], str):
                    evidence_items.append({"type": k, "paths": v})
                elif isinstance(v, (int, float)):
                    evidence_items.append({"type": k, "value": v})
            state.evidence = evidence_items

            state.add_step(
                stage="evidence_generation",
                action=f"Compiled {len(state.evidence)} evidence artifacts and spatial statistics",
                status="completed"
            )

            # 7. Grounded Natural-Language Response Generation
            yield {"event": "status", "data": {"stage": "response_generation"}}
            SafetyPolicy.check_loop_safety(state.execution_steps)
            answer = await self.response_generator.generate_response(state)
            state.final_response = answer
            state.status = "completed"

            # 8. Persist conversation and run history if database session provided
            if db:
                try:
                    result_path = evidence_dict.get("change_mask") or evidence_dict.get("segmentation_mask") or evidence_dict.get("fused_raster")
                    await conversation_service.record_orchestration_run(
                        db=db,
                        request_id=state.request_id,
                        task=state.selected_task or "unknown",
                        model=state.selected_model or "unknown",
                        provider=state.provider_used,
                        status=state.status,
                        duration_ms=state.total_duration_ms,
                        fallback_used=state.fallback_used,
                        steps=[s.model_dump() for s in state.execution_steps],
                        conversation_id=state.conversation_id,
                        errors=state.errors,
                        result_path=result_path
                    )
                    if state.conversation_id:
                        # Append assistant message
                        await conversation_service.add_message(
                            conversation_id=state.conversation_id,
                            role="assistant",
                            content=answer,
                            db=db,
                            imagery_ids=state.available_inputs,
                            task=state.selected_task
                        )
                except Exception as db_err:
                    logger.warning("Could not persist orchestration run in DB: %s", db_err)

            state.finalize()
            yield {"event": "completed", "data": state.to_safe_dict()}

        except (OrchestrationStalledError, AIExecutionFailedError, OutputValidationError, InsufficientSpatialOverlapError) as controlled_err:
            state.status = "failed"
            state.errors.append(str(controlled_err))
            state.final_response = f"Analysis halted: {str(controlled_err)}"
            state.finalize()
            yield {"event": "failed", "data": state.to_safe_dict()}
        except Exception as unhandled:
            logger.error("Unhandled error in orchestration: %s", unhandled)
            state.status = "failed"
            state.errors.append(str(unhandled))
            state.final_response = f"Analysis error encountered: {str(unhandled)}"
            state.finalize()
            yield {"event": "failed", "data": state.to_safe_dict()}


orchestrator = OrbitMindOrchestrator()
