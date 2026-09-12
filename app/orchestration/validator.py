import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from app.core.logging import logger
from app.geospatial.crs import are_crs_equal, parse_crs
from app.geospatial.raster import read_raster_metadata
from app.geospatial.reprojection import check_spatial_overlap
from app.orchestration.policies import InsufficientSpatialOverlapError


class OutputValidationError(Exception):
    """Raised when model inference output fails structural or mathematical validity checks."""
    pass


class OutputValidator:
    """
    Validates model outputs, geospatial consistency, and data integrity.
    Prevents corrupt or invalid model outputs from propagating downstream.
    """

    def validate_geospatial_inputs(self, imagery_paths: List[str]) -> None:
        """Ensures input rasters exist, have valid metadata, and overlap spatially if multi-temporal."""
        if not imagery_paths:
            raise OutputValidationError("No imagery paths provided for validation.")

        metas = []
        for path_str in imagery_paths:
            p = Path(path_str)
            if not p.exists():
                raise FileNotFoundError(f"Input imagery does not exist on disk: {path_str}")
            meta = read_raster_metadata(p)
            metas.append(meta)

        if len(metas) >= 2:
            m1, m2 = metas[0], metas[1]
            if m1.get("is_georeferenced") and m2.get("is_georeferenced"):
                overlap = check_spatial_overlap(m1["bounds"], m2["bounds"])
                if not overlap:
                    raise InsufficientSpatialOverlapError(
                        f"Input images do not overlap spatially: {m1['bounds']} vs {m2['bounds']}"
                    )

    def validate_model_output(self, task: str, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates output produced by a specialist remote-sensing model.
        Checks structure, data types, confidence scores, and artifact validity.
        """
        if not isinstance(raw_output, dict):
            raise OutputValidationError(f"Expected model output dictionary, got: {type(raw_output)}")

        confidence = raw_output.get("confidence")
        if confidence is None or not isinstance(confidence, (int, float)) or math.isnan(confidence) or math.isinf(confidence):
            raise OutputValidationError(f"Invalid model confidence score: {confidence}")
        if not (0.0 <= confidence <= 1.0):
            raise OutputValidationError(f"Confidence score {confidence} outside valid range [0.0, 1.0]")

        # Task-specific artifact verification
        if task == "change_detection":
            evidence = raw_output.get("evidence", {})
            mask_path = evidence.get("change_mask")
            if not mask_path or not isinstance(mask_path, str):
                raise OutputValidationError("Change detection model output must contain valid 'change_mask' file path.")
            if not Path(mask_path).exists():
                raise OutputValidationError(f"Generated change mask file does not exist: {mask_path}")

            stats = raw_output.get("statistics", {})
            if not stats or "changed_area_km2" not in stats:
                raise OutputValidationError("Change detection output must include 'changed_area_km2' in statistics.")

        elif task == "segmentation":
            evidence = raw_output.get("evidence", {})
            mask_path = evidence.get("segmentation_mask")
            if not mask_path or not Path(mask_path).exists():
                raise OutputValidationError("Segmentation model output must produce a valid segmentation mask file.")

        elif task == "vqa":
            summary = raw_output.get("summary")
            if not summary or not isinstance(summary, str) or len(summary.strip()) == 0:
                raise OutputValidationError("VQA model output must provide non-empty answer text.")

        elif task == "captioning":
            summary = raw_output.get("summary")
            if not summary or not isinstance(summary, str) or len(summary.strip()) == 0:
                raise OutputValidationError("Captioning model must provide non-empty caption.")

        elif task == "optical_sar":
            evidence = raw_output.get("evidence", {})
            fused_path = evidence.get("fused_raster")
            if not fused_path or not Path(fused_path).exists():
                raise OutputValidationError("Optical + SAR analysis must generate a valid fused composite GeoTIFF.")

        elif task == "cloud_removal":
            evidence = raw_output.get("evidence", {})
            mask_path = evidence.get("cloud_mask")
            if not mask_path or not Path(mask_path).exists():
                raise OutputValidationError("Cloud removal must produce a valid cloud mask file.")

        elif task == "comprehensive_analysis":
            evidence = raw_output.get("evidence", {})
            if not evidence:
                raise OutputValidationError("Comprehensive analysis must generate evidence artifacts across specialists.")

        logger.info("Successfully validated model output for task '%s' (Confidence: %.2f)", task, confidence)
        return {"is_valid": True, "task": task, "confidence": confidence}
