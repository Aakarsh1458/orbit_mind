import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.llm.router import WorkloadStage, llm_router
from app.orchestration.state import OrchestrationState
from app.services.query_service import query_service


class StructuredIntent(BaseModel):
    """Strict schema for remote sensing query intent and requirement formulation."""
    intent: str = Field(..., description="VQA, CAPTIONING, CHANGE_DETECTION, SEGMENTATION, OPTICAL_SAR, or UNKNOWN")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    required_inputs: List[str] = Field(default_factory=list, description="e.g. ['temporal_image_1', 'temporal_image_2']")
    required_capabilities: List[str] = Field(default_factory=list, description="e.g. ['change_detection']")
    requires_imagery: bool = True
    time_constraints: Optional[str] = None
    geographic_constraints: Optional[str] = None


class TaskPlanner:
    """
    Formulates a structured execution plan for incoming remote sensing queries.
    Determines required capabilities, checks imagery availability, and identifies missing inputs.
    """

    INTENT_MAP = {
        "change_detection": "CHANGE_DETECTION",
        "segmentation": "SEGMENTATION",
        "vqa": "VQA",
        "captioning": "CAPTIONING",
        "optical_sar": "OPTICAL_SAR",
        "cloud_removal": "CLOUD_REMOVAL",
        "comprehensive_analysis": "COMPREHENSIVE_ANALYSIS",
        "unknown": "UNKNOWN"
    }

    REQUIRED_INPUT_COUNTS = {
        "CHANGE_DETECTION": 2,
        "OPTICAL_SAR": 2,
        "SEGMENTATION": 1,
        "VQA": 1,
        "CAPTIONING": 1,
        "CLOUD_REMOVAL": 1,
        "COMPREHENSIVE_ANALYSIS": 1
    }

    async def understand_and_plan(self, state: OrchestrationState) -> OrchestrationState:
        t0 = time.perf_counter()

        # Step 1: Intent Understanding (Rule-based or LLM structured output via Stage 1)
        rule_result = query_service.understand_query(state.user_query)
        detected_task = rule_result["selected_analysis"]
        canonical_intent = self.INTENT_MAP.get(detected_task, "UNKNOWN")

        # Stage 1: If ambiguous or running in production with LLM configured, extract structured schema
        if canonical_intent == "UNKNOWN" and (settings.GEMINI_API_KEY or settings.OPENROUTER_API_KEY):
            try:
                schema_res = await llm_router.route_structured(
                    stage=WorkloadStage.STAGE_1_QUERY_UNDERSTANDING,
                    messages=[
                        {"role": "system", "content": "Extract remote sensing intent, task, and requirements."},
                        {"role": "user", "content": state.user_query}
                    ],
                    response_model=StructuredIntent,
                    temperature=0.0
                )
                parsed_intent: StructuredIntent = schema_res["parsed"]
                if parsed_intent.intent in self.INTENT_MAP.values():
                    canonical_intent = parsed_intent.intent
                    detected_task = canonical_intent.lower()
                    rule_result["confidence"] = parsed_intent.confidence
            except Exception as e:
                logger.info("Stage 1 structured intent extraction fallback to rule base: %s", e)

        # Required inputs inference
        min_required = self.REQUIRED_INPUT_COUNTS.get(canonical_intent, 1)
        req_inputs = [f"satellite_image_{i+1}" for i in range(min_required)]
        if canonical_intent == "CHANGE_DETECTION":
            req_inputs = ["temporal_image_1", "temporal_image_2"]
        elif canonical_intent == "OPTICAL_SAR":
            req_inputs = ["optical_imagery", "sar_imagery"]

        state.detected_intent = canonical_intent
        state.intent_confidence = rule_result["confidence"]
        state.selected_task = detected_task
        state.required_inputs = req_inputs

        duration = (time.perf_counter() - t0) * 1000
        state.add_step(
            stage="query_understanding",
            action=f"Classified query into task: {detected_task} (Intent: {canonical_intent})",
            status="completed",
            duration_ms=duration
        )

        # Stage 2: Complex Task Planning & Spatial Disambiguation (Claude 3.5 Sonnet -> Gemini 1.5 Pro)
        if canonical_intent in ("COMPREHENSIVE_ANALYSIS", "CHANGE_DETECTION", "OPTICAL_SAR") and (settings.OPENROUTER_API_KEY or settings.GEMINI_API_KEY):
            try:
                await llm_router.route_chat(
                    stage=WorkloadStage.STAGE_2_TASK_PLANNING,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a Geospatial Systems Planner. Validate temporal dependencies, "
                                "coordinate reference system requirements, and band alignment constraints."
                            )
                        },
                        {"role": "user", "content": f"Query: {state.user_query}\nTask: {detected_task}"}
                    ],
                    temperature=0.1,
                    max_tokens=256
                )
            except Exception as e:
                logger.info("Stage 2 complex planning fallback: %s", e)

        # Step 2: Validate Available Inputs
        avail_count = len(state.available_inputs)
        logger.info(
            "Task %s requires %d inputs. Available inputs: %d",
            canonical_intent, min_required, avail_count
        )

        if avail_count < min_required:
            state.status = "needs_input"
            if canonical_intent == "CHANGE_DETECTION":
                state.final_response = (
                    f"Change detection requires 2 temporal satellite images (before & after), "
                    f"but only {avail_count} was provided. Please provide the required second image."
                )
            elif canonical_intent == "OPTICAL_SAR":
                state.final_response = (
                    f"Optical + SAR analysis requires at least 1 Optical dataset and 1 SAR radar dataset. "
                    f"Please upload both datasets to proceed."
                )
            else:
                state.final_response = "At least one satellite image is required to perform this analysis."

            state.follow_up_suggestions = [
                "Load SEN12MS-CR benchmark sample",
                "Perform all 6 remote sensing models",
                "Run land cover segmentation"
            ]
            state.add_step(
                stage="planning",
                action="Input validation identified missing required satellite imagery",
                status="needs_input"
            )
            return state

        state.add_step(
            stage="planning",
            action=f"Created execution plan for {detected_task} with {avail_count} input datasets",
            status="completed"
        )
        return state
