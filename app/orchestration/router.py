import time
from typing import Any, Dict, List, Optional

from app.ai.registry import model_registry
from app.core.config import settings
from app.core.logging import logger
from app.orchestration.state import OrchestrationState


class ModelRouter:
    """
    Selects the optimal specialist remote-sensing AI model based on task requirements,
    input modalities, sensor types, and available hardware acceleration.
    Identifies eligible fallback models for fault tolerance.
    """

    def route_model(self, state: OrchestrationState) -> OrchestrationState:
        t0 = time.perf_counter()
        task = state.selected_task or "change_detection"

        if task == "comprehensive_analysis":
            state.selected_model = "comprehensive_6_model_suite"
            state.fallback_model = None
            duration = (time.perf_counter() - t0) * 1000
            state.add_step(
                stage="model_selection",
                action="Routed to Comprehensive 6-Model Suite (Segmentation, Change Detection, Captioning, VQA, Optical+SAR, Cloud Removal)",
                status="completed",
                duration_ms=duration
            )
            return state

        # Query registry for primary model
        primary_model = model_registry.get_model(task, mode=settings.AI_MODE)
        meta = primary_model.get_metadata()
        caps = primary_model.get_capabilities()

        device = settings.get_effective_device()
        logger.info(
            "Routing task '%s' to primary model '%s' (Device: %s, Mode: %s)",
            task, meta.get("name", primary_model.__class__.__name__), device, settings.AI_MODE
        )

        state.selected_model = meta.get("name", primary_model.__class__.__name__)

        # Check for eligible fallback model
        fallback_inst = model_registry.get_fallback_model(task, mode=settings.AI_MODE)
        if fallback_inst:
            fb_meta = fallback_inst.get_metadata()
            state.fallback_model = fb_meta.get("name", fallback_inst.__class__.__name__)
        else:
            state.fallback_model = None

        duration = (time.perf_counter() - t0) * 1000
        state.add_step(
            stage="model_selection",
            action=f"Selected model: {state.selected_model} (Fallback: {state.fallback_model or 'None'})",
            status="completed",
            duration_ms=duration
        )
        return state
