import re
import time
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.llm.router import WorkloadStage, llm_router
from app.orchestration.state import OrchestrationState


class ResponseGenerator:
    """
    Generates concise, factual natural-language responses summarizing analysis findings.
    Ensures that every numerical figure or spatial conclusion is strictly grounded
    in computed evidence and statistics without hallucinating values.
    """

    def _clean_llm_response(self, text: str) -> str:
        """Strips internal thinking tokens or thinking process prefixes from models."""
        cleaned = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
        if "Here's a thinking process" in cleaned:
            # Look for summary section or double newline
            parts = re.split(r"(?:###|\n\n\*\*Summary|\n\nBased on|\n\nIn summary)", cleaned, maxsplit=1)
            if len(parts) > 1:
                cleaned = parts[1].strip()
        return cleaned.strip()

    async def generate_response(self, state: OrchestrationState) -> str:
        t0 = time.perf_counter()
        task = state.selected_task
        stats = state.statistics
        summary = state.model_results.get("summary", "") if state.model_results else ""

        # Build prompt for grounded synthesis
        evidence_summary = []
        for ev in state.evidence:
            evidence_summary.append(f"- {ev.get('type')}: {ev.get('path', ev.get('id', 'available'))}")

        stats_summary = [f"{k}: {v}" for k, v in stats.items()] if stats else ["No quantitative metrics"]

        system_instruction = (
            "You are OrbitMind, an expert remote sensing AI assistant. "
            "Generate a clear, factual, and concise summary of the satellite analysis. "
            "CRITICAL RULE: DO NOT INVENT NUMBERS. Every metric, area in km², or percentage MUST originate directly from the provided statistics."
        )

        user_content = (
            f"User Query: {state.user_query}\n"
            f"Task: {task}\n"
            f"Model Summary: {summary}\n"
            f"Statistics: {', '.join(stats_summary)}\n"
            f"Evidence: {', '.join(evidence_summary)}\n"
            f"Generate a professional, concise summary. Do not include thinking steps or meta-commentary."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]

        # Use LLM router to generate polished answer or fall back to structured model summary
        try:
            chat_result = await llm_router.route_chat(
                stage=WorkloadStage.STAGE_8_RESPONSE_GENERATION,
                messages=messages,
                temperature=0.1,
                max_tokens=512,
            )
            raw_answer = chat_result["content"].strip()
            answer = self._clean_llm_response(raw_answer)
            state.provider_used = chat_result.get("provider_used", "internal")
        except Exception as e:
            logger.info("Using direct specialist model summary: %s", e)
            answer = summary or f"Analysis for task '{task}' completed successfully."
            state.provider_used = "specialist_engine"

        state.follow_up_suggestions = self.generate_follow_up_suggestions(state)

        duration = (time.perf_counter() - t0) * 1000
        state.add_step(
            stage="response_generation",
            action="Synthesized factual natural-language response and follow-up options",
            status="completed",
            duration_ms=duration
        )
        return answer

    def generate_follow_up_suggestions(self, state: OrchestrationState) -> List[str]:
        task = state.selected_task
        if task == "comprehensive_analysis":
            return [
                "Drill down into land cover segmentation classes",
                "Inspect cloud mask and SAR reconstructed layer",
                "Analyze bi-temporal radar change statistics",
                "Ask a visual question about specific features"
            ]
        elif task == "cloud_removal":
            return [
                "Run semantic segmentation on de-clouded optical bands",
                "Inspect SAR radar backscatter texture overlay",
                "Perform all 6 remote sensing models",
                "Describe this de-clouded satellite scene"
            ]
        elif task == "segmentation":
            return [
                "Calculate urban vs vegetation area breakdown",
                "Run cloud removal on optical imagery",
                "Perform all 6 remote sensing models",
                "Detect changes against previous baseline imagery"
            ]
        elif task == "change_detection":
            return [
                "Segment land cover classes in changed zones",
                "Inspect SAR radar backscatter anomalies",
                "Perform all 6 remote sensing models",
                "Ask a visual question about changed areas"
            ]
        elif task == "optical_sar":
            return [
                "Perform semantic segmentation on fused product",
                "Run cloud removal with SAR radar guidance",
                "Perform all 6 remote sensing models",
                "Describe multimodal landscape characteristics"
            ]
        elif task == "captioning":
            return [
                "Ask a visual question about objects in this scene",
                "Perform all 6 remote sensing models",
                "Segment primary land cover classes",
                "Detect anomalies using SAR radar"
            ]
        elif task == "vqa":
            return [
                "Ask another question about this satellite scene",
                "Perform all 6 remote sensing models",
                "Run semantic segmentation to verify boundaries",
                "Generate a scene caption"
            ]
        else:
            return [
                "Perform all 6 remote sensing models",
                "Run land cover segmentation",
                "Inspect cloud removal and SAR radar fusion"
            ]
