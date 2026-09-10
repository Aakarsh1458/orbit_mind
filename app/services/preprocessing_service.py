from pathlib import Path
from typing import Any, Dict, List, Tuple
from app.core.logging import logger
from app.geospatial.crs import are_crs_equal
from app.geospatial.reprojection import align_rasters, check_spatial_overlap
from app.models.imagery import Imagery


class PreprocessingService:
    """Service handling multi-raster validation, CRS alignment, and spatial preprocessing."""

    def validate_and_prepare_inputs(
        self,
        analysis_type: str,
        imagery_records: List[Imagery],
        output_dir: Path
    ) -> List[str]:
        """
        Validates imagery records for the specified analysis type and performs
        geospatial alignment where required. Returns ready-to-process filepaths.
        """
        if not imagery_records:
            raise ValueError("No imagery records provided for analysis.")

        # Single-image tasks
        if analysis_type in ("vqa", "captioning", "segmentation"):
            first_record = imagery_records[0]
            if not Path(first_record.path).exists():
                raise FileNotFoundError(f"Imagery file does not exist: {first_record.path}")
            return [first_record.path]

        # Multi-image tasks (change_detection, optical_sar)
        if analysis_type in ("change_detection", "optical_sar"):
            if len(imagery_records) < 2:
                raise ValueError(
                    f"Analysis task '{analysis_type}' requires at least 2 imagery datasets, got {len(imagery_records)}."
                )

            rec1, rec2 = imagery_records[0], imagery_records[1]
            path1, path2 = Path(rec1.path), Path(rec2.path)

            if not path1.exists() or not path2.exists():
                raise FileNotFoundError("One or more imagery files are missing from storage.")

            # Spatial overlap check
            if rec1.is_georeferenced and rec2.is_georeferenced:
                if not check_spatial_overlap(rec1.bounds, rec2.bounds):
                    raise ValueError(
                        f"Input images do not overlap spatially. Bounds 1: {rec1.bounds} vs Bounds 2: {rec2.bounds}"
                    )

            # Check if alignment is needed
            paths = [str(path1), str(path2)]
            if (
                not are_crs_equal(rec1.crs, rec2.crs)
                or rec1.width != rec2.width
                or rec1.height != rec2.height
            ):
                aligned_path2 = output_dir / f"aligned_{path2.name}"
                logger.info("Aligning %s to match reference grid of %s", path2.name, path1.name)
                align_rasters(path1, path2, aligned_path2)
                paths = [str(path1), str(aligned_path2)]

            return paths

        # Fallback for unknown analysis types
        return [r.path for r in imagery_records]


preprocessing_service = PreprocessingService()
