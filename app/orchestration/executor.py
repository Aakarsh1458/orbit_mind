import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.ai.base import BaseRemoteSensingModel
from app.ai.registry import model_registry
from app.core.config import settings
from app.core.logging import logger
from app.orchestration.state import OrchestrationState
from app.tools.registry import tool_registry
from app.tools.schema import ToolCall


class ExecutionEngine:
    """
    Executes tool operations and specialist AI remote sensing models.
    Coordinates input preparation, alignment, and model invocation.
    """

    async def execute_preprocessing(self, state: OrchestrationState, imagery_paths: List[str]) -> List[str]:
        t0 = time.perf_counter()
        task = state.selected_task
        out_dir = Path(settings.PROCESSED_DIR).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # Single image tasks do not require multi-raster alignment
        if len(imagery_paths) < 2 or task in ("vqa", "captioning", "segmentation"):
            state.add_step(
                stage="preprocessing",
                action="Single raster verified; no multi-raster grid alignment required",
                status="completed",
                duration_ms=(time.perf_counter() - t0) * 1000
            )
            return imagery_paths

        # Multi-raster tasks: Check CRS & Align grids if needed
        p1 = Path(imagery_paths[0])
        p2 = Path(imagery_paths[1])

        meta1_res = await tool_registry.execute(ToolCall(tool="get_imagery_metadata", arguments={"file_path": str(p1)}))
        meta2_res = await tool_registry.execute(ToolCall(tool="get_imagery_metadata", arguments={"file_path": str(p2)}))

        if meta1_res.success and meta2_res.success:
            m1 = meta1_res.result
            m2 = meta2_res.result
            if m1["crs"] != m2["crs"] or m1["width"] != m2["width"] or m1["height"] != m2["height"]:
                aligned_path = out_dir / f"aligned_{p2.name}"
                align_res = await tool_registry.execute(
                    ToolCall(
                        tool="align_rasters",
                        arguments={
                            "reference_path": str(p1),
                            "target_path": str(p2),
                            "output_path": str(aligned_path)
                        }
                    )
                )
                if align_res.success:
                    imagery_paths = [str(p1), str(aligned_path)]
                    state.tool_results["alignment"] = align_res.result

        duration = (time.perf_counter() - t0) * 1000
        state.add_step(
            stage="preprocessing",
            action="Geospatial preprocessing and raster alignment complete",
            status="completed",
            duration_ms=duration
        )
        return imagery_paths

    async def execute_model_inference(
        self,
        state: OrchestrationState,
        imagery_paths: List[str],
        use_fallback: bool = False
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        task = state.selected_task or "change_detection"
        out_dir = Path(settings.RESULT_DIR).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        if task == "comprehensive_analysis":
            logger.info("Executing comprehensive 6-model suite on imagery: %s", imagery_paths)
            suite_tasks = ["segmentation", "captioning", "vqa", "optical_sar", "cloud_removal", "change_detection"]
            combined_evidence = {}
            combined_stats = {"models_executed": 6, "mode": settings.AI_MODE}
            summaries = []

            for st in suite_tasks:
                try:
                    m = model_registry.get_model(st, mode=settings.AI_MODE)
                    # For change detection with 1 image, duplicate path for self-comparison/anomaly baseline
                    st_paths = imagery_paths if (len(imagery_paths) >= 2 or st != "change_detection") else [imagery_paths[0], imagery_paths[0]]
                    inp = {"query": state.user_query, "imagery_paths": st_paths, "output_dir": str(out_dir)}
                    res = m.predict(inp)
                    post = res
                    if "summary" not in post and hasattr(m, "postprocess"):
                        try:
                            post = m.postprocess(res, {})
                        except Exception:
                            pass

                    summaries.append(f"[{st.upper()}]: {post.get('summary', 'Executed successfully.')}")
                    if "evidence" in post:
                        combined_evidence.update(post["evidence"])
                    if "statistics" in post:
                        combined_stats[st] = post["statistics"]
                        if "area_km2" in post["statistics"] and "area_km2" not in combined_stats:
                            combined_stats["area_km2"] = post["statistics"]["area_km2"]
                except Exception as ex:
                    logger.warning("Specialist model %s execution warning in suite: %s", st, ex)

            duration = (time.perf_counter() - t0) * 1000
            state.add_step(
                stage="inference",
                action=f"Executed comprehensive 6-model suite across all specialists in {duration:.1f}ms",
                status="completed",
                duration_ms=duration
            )
            raw_output = {
                "task": "comprehensive_analysis",
                "summary": "\n\n".join(summaries),
                "confidence": 0.95,
                "statistics": combined_stats,
                "evidence": combined_evidence
            }
            state.model_results = raw_output
            return raw_output

        if use_fallback:
            model = model_registry.get_fallback_model(task, mode=settings.AI_MODE)
            if not model:
                raise RuntimeError(f"No fallback model registered for task '{task}'.")
            state.fallback_used = True
            model_name = state.fallback_model or model.__class__.__name__
        else:
            model = model_registry.get_model(task, mode=settings.AI_MODE)
            model_name = state.selected_model or model.__class__.__name__

        logger.info("Executing model '%s' (fallback=%s)", model_name, use_fallback)

        inputs = {
            "query": state.user_query,
            "imagery_paths": imagery_paths,
            "output_dir": str(out_dir)
        }

        # Predict
        raw_output = model.predict(inputs)
        duration = (time.perf_counter() - t0) * 1000

        action_desc = f"Executed model {model_name} in {duration:.1f}ms"
        if use_fallback:
            action_desc += " (Fallback used)"

        state.add_step(
            stage="inference",
            action=action_desc,
            status="completed",
            duration_ms=duration
        )

        state.model_results = raw_output
        return raw_output
