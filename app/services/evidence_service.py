from typing import Any, Dict, List
from app.core.logging import logger


class EvidenceService:
    """Service packaging model evidence, geographic masks, footprints, and provenance."""

    def compile_evidence(
        self,
        model_output: Dict[str, Any],
        imagery_paths: List[str]
    ) -> Dict[str, Any]:
        evidence = model_output.get("evidence", {})
        if "source_images" not in evidence:
            evidence["source_images"] = imagery_paths

        return evidence


evidence_service = EvidenceService()
