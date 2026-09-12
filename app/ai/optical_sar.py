from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from app.ai.base import BaseRemoteSensingModel, ModelUnavailableError
from app.core.config import settings
from app.core.logging import logger
from app.geospatial.raster import read_bands, read_raster_metadata, write_geotiff
from app.geospatial.crs import are_crs_equal
from app.geospatial.reprojection import align_rasters, check_spatial_overlap


class OpticalSARModel(BaseRemoteSensingModel):
    """
    Specialist model for Optical + Synthetic Aperture Radar (SAR) multimodal fusion analysis.
    Combines optical spectral bands with radar backscatter (VV/VH polarizations)
    for all-weather cloud-penetrating surface assessment.
    """

    def __init__(self, mode: str = "mock"):
        super().__init__(mode=mode)
        self.model_name = "OrbitMind-Optical-SAR-Fusion-v1"

    def load(self) -> None:
        if self.mode == "production":
            logger.info("Production mode: Loading multimodal Optical-SAR fusion neural network...")
            self.is_loaded = True
        else:
            logger.info("Mock mode: Initializing Optical-SAR multimodal pipeline.")
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        imagery_paths = inputs.get("imagery_paths", [])
        if len(imagery_paths) < 2:
            raise ValueError(
                "Optical + SAR analysis requires at least 2 imagery inputs (1 Optical dataset and 1 SAR dataset)."
            )

        for p in imagery_paths[:2]:
            if not Path(p).exists():
                raise FileNotFoundError(f"Input imagery file not found: {p}")
        return True

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(inputs)
        output_dir = Path(inputs.get("output_dir", "./data/results")).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        optical_path = Path(inputs["imagery_paths"][0])
        sar_path = Path(inputs["imagery_paths"][1])

        meta_opt = read_raster_metadata(optical_path)
        meta_sar = read_raster_metadata(sar_path)

        # Validate spatial overlap
        if meta_opt.get("is_georeferenced") and meta_sar.get("is_georeferenced"):
            if not check_spatial_overlap(meta_opt["bounds"], meta_sar["bounds"]):
                raise ValueError("Optical and SAR scenes do not spatially overlap.")

        # Align SAR to Optical grid
        aligned_sar_path = sar_path
        if (
            not are_crs_equal(meta_opt["crs"], meta_sar["crs"])
            or meta_opt["width"] != meta_sar["width"]
            or meta_opt["height"] != meta_sar["height"]
        ):
            aligned_sar_path = output_dir / f"aligned_sar_{sar_path.name}"
            align_rasters(optical_path, sar_path, aligned_sar_path)
            meta_sar = read_raster_metadata(aligned_sar_path)

        if self.mode == "production":
            raise ModelUnavailableError(
                f"Production Optical-SAR multimodal fusion model weights are not loaded. "
                f"Mount weights in {settings.MODEL_CACHE_DIR} or enable AI_MODE=mock.",
                status_code="MODEL_UNAVAILABLE"
            )
        else:
            # Deterministic fusion evidence generation
            arr_opt = read_bands(optical_path).astype(np.float32)
            arr_sar = read_bands(aligned_sar_path).astype(np.float32)

            # Generate synthetic fused composite (e.g. Red=Optical band 1, Green=Optical band 2, Blue=SAR band 1)
            h, w = meta_opt["height"], meta_opt["width"]
            fused_bands = np.zeros((3, h, w), dtype=np.uint8)

            b1 = arr_opt[0] if arr_opt.shape[0] > 0 else np.zeros((h, w))
            b2 = arr_opt[1] if arr_opt.shape[0] > 1 else b1
            sar_b1 = arr_sar[0] if arr_sar.shape[0] > 0 else b1

            def norm_u8(a):
                mn, mx = np.min(a), np.max(a)
                if mx - mn == 0:
                    return np.zeros_like(a, dtype=np.uint8)
                return np.clip(((a - mn) / (mx - mn)) * 255.0, 0, 255).astype(np.uint8)

            fused_bands[0] = norm_u8(b1)
            fused_bands[1] = norm_u8(b2)
            fused_bands[2] = norm_u8(sar_b1)

            confidence = 0.87

        # Save fused GeoTIFF artifact
        fused_path = output_dir / f"fused_opt_sar_{optical_path.stem}.tif"
        write_geotiff(
            output_path=fused_path,
            data=fused_bands,
            transform=meta_opt["transform"],
            crs=meta_opt["crs"],
            dtype="uint8"
        )

        return self.postprocess(
            raw_output={
                "fused_path": str(fused_path),
                "confidence": confidence,
                "optical_source": str(optical_path),
                "sar_source": str(aligned_sar_path),
                "crs": meta_opt["crs"]
            },
            metadata=meta_opt
        )

    def postprocess(self, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        summary = (
            f"Successfully aligned and fused Optical imagery ({metadata['bands']} bands) "
            f"with SAR radar backscatter. Generated 3-band false-color composite."
        )

        return {
            "mode": self.mode,
            "model": self.model_name,
            "summary": summary,
            "confidence": raw_output["confidence"],
            "statistics": {
                "optical_bands": metadata["bands"],
                "fused_dimensions": f"{metadata['width']}x{metadata['height']}",
                "crs": raw_output["crs"]
            },
            "evidence": {
                "fused_raster": raw_output["fused_path"],
                "source_optical": raw_output["optical_source"],
                "source_sar": raw_output["sar_source"],
                "crs": raw_output["crs"]
            }
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "task": "optical_sar",
            "mode": self.mode,
            "inputs": ["Optical (RGB/NIR)", "SAR (VV/VH)"],
            "output_formats": ["GeoTIFF Composite", "JSON"]
        }

    def get_capabilities(self):
        from app.ai.base import ModelCapability
        return ModelCapability(
            tasks=["optical_sar"],
            modalities=["optical", "sar"],
            input_formats=["raster", "geotiff"],
            output_formats=["fused_composite", "geotiff"],
            min_inputs=2,
            max_inputs=2,
            supported_sensors=["Sentinel-1", "Sentinel-2", "Landsat"],
            supports_gpu=True,
            supports_cpu=True
        )
