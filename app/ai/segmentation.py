from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from app.ai.base import BaseRemoteSensingModel
from app.core.logging import logger
from app.geospatial.raster import read_bands, read_raster_metadata, write_geotiff
from app.geospatial.statistics import calculate_segmentation_statistics
from app.geospatial.vector import polygonize_mask


class SegmentationModel(BaseRemoteSensingModel):
    """
    Specialist model for land cover and geographic feature semantic segmentation.
    Identifies classes: water, vegetation, buildings, roads, unknown.
    """

    CLASS_MAP = {
        0: "unknown",
        1: "water",
        2: "vegetation",
        3: "buildings",
        4: "roads"
    }

    def __init__(self, mode: str = "mock"):
        super().__init__(mode=mode)
        self.model_name = "OrbitMind-LandCover-Segmenter-v1"

    def load(self) -> None:
        if self.mode == "production":
            logger.info("Production mode: Loading semantic segmentation neural network weights...")
            self.is_loaded = True
        else:
            logger.info("Mock mode: Initializing spectral clustering baseline segmentation.")
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        imagery_paths = inputs.get("imagery_paths", [])
        if not imagery_paths:
            raise ValueError("Segmentation requires at least one satellite image input.")

        path = Path(imagery_paths[0])
        if not path.exists():
            raise FileNotFoundError(f"Input imagery file not found: {path}")

        return True

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(inputs)
        img_path = Path(inputs["imagery_paths"][0])
        output_dir = Path(inputs.get("output_dir", "./data/results")).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        meta = read_raster_metadata(img_path)
        arr = read_bands(img_path)

        if self.mode == "production":
            raise NotImplementedError(
                "Production segmentation weights are not configured. "
                "Provide model weights or set AI_MODE=mock."
            )
        else:
            # Deterministic mock segmentation using band thresholds / spatial partition
            height, width = meta["height"], meta["width"]
            seg_mask = np.zeros((height, width), dtype=np.uint8)

            # Assign synthetic class labels deterministically
            # Water (class 1) in bottom quadrant
            seg_mask[int(height * 0.7):, :] = 1
            # Vegetation (class 2) in top left
            seg_mask[:int(height * 0.5), :int(width * 0.5)] = 2
            # Buildings (class 3) in center
            seg_mask[int(height * 0.3):int(height * 0.7), int(width * 0.4):int(width * 0.8)] = 3
            # Roads (class 4) intersecting strip
            seg_mask[int(height * 0.5):int(height * 0.55), :] = 4

            confidence = 0.84

        # Write segmentation GeoTIFF mask
        mask_filename = f"seg_mask_{img_path.stem}.tif"
        mask_path = output_dir / mask_filename

        write_geotiff(
            output_path=mask_path,
            data=seg_mask,
            transform=meta["transform"],
            crs=meta["crs"],
            nodata=255,
            dtype="uint8"
        )

        # Compute statistics
        res_x, res_y = meta["resolution"]
        stats = calculate_segmentation_statistics(
            seg_mask=seg_mask,
            class_mapping=self.CLASS_MAP,
            pixel_res_x=res_x,
            pixel_res_y=res_y,
            crs=meta["crs"]
        )

        return self.postprocess(
            raw_output={
                "mask_path": str(mask_path),
                "confidence": confidence,
                "statistics": stats,
                "source_image": str(img_path),
                "crs": meta["crs"]
            },
            metadata=meta
        )

    def postprocess(self, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        classes = raw_output["statistics"]["classes"]
        summary_items = [f"{cls}: {info['area_km2']:.2f} km² ({info['percentage']}%)" for cls, info in classes.items() if info["pixels"] > 0]
        summary = f"Semantic segmentation classified land cover into: {', '.join(summary_items)}."

        return {
            "mode": self.mode,
            "model": self.model_name,
            "summary": summary,
            "confidence": raw_output["confidence"],
            "statistics": raw_output["statistics"],
            "evidence": {
                "segmentation_mask": raw_output["mask_path"],
                "source_images": [raw_output["source_image"]],
                "crs": raw_output["crs"]
            }
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "task": "segmentation",
            "mode": self.mode,
            "classes": self.CLASS_MAP,
            "output_formats": ["GeoTIFF", "JSON"]
        }
