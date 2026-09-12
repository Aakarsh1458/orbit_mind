from pathlib import Path
from typing import Any, Dict, List
from app.ai.base import BaseRemoteSensingModel, ModelUnavailableError
from app.core.config import settings
from app.core.logging import logger
from app.geospatial.raster import read_raster_metadata


class CaptioningModel(BaseRemoteSensingModel):
    """
    Satellite image captioning specialist model.
    Generates descriptive natural language summaries of remote sensing scenes.
    """

    def __init__(self, mode: str = "mock"):
        super().__init__(mode=mode)
        self.model_name = "OrbitMind-RS-Captioner-v1"

    def load(self) -> None:
        if self.mode == "production":
            logger.info("Production mode: Initializing satellite captioning vision encoder...")
            self.is_loaded = True
        else:
            logger.info("Mock mode: Initializing descriptive scene summarizer.")
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        imagery_paths = inputs.get("imagery_paths", [])
        if not imagery_paths:
            raise ValueError("Captioning requires at least one satellite image input.")
        if not Path(imagery_paths[0]).exists():
            raise FileNotFoundError(f"Input image file does not exist: {imagery_paths[0]}")
        return True

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(inputs)
        img_path = Path(inputs["imagery_paths"][0])
        meta = read_raster_metadata(img_path)

        if self.mode == "production":
            raise ModelUnavailableError(
                f"Production captioning checkpoint not configured. "
                f"Mount weights in {settings.MODEL_CACHE_DIR} or set AI_MODE=mock.",
                status_code="MODEL_UNAVAILABLE"
            )
        else:
            confidence = 0.89
            res_str = f"{meta['resolution'][0]:.2f}m" if "resolution" in meta else "medium"
            caption = (
                f"High-resolution multispectral scene ({meta['width']}x{meta['height']} px, {meta['bands']} bands) "
                f"capturing structured settlement zones, surrounding vegetation patches, and linear transit corridors."
            )

        return self.postprocess(
            raw_output={
                "caption": caption,
                "confidence": confidence,
                "source_image": str(img_path)
            },
            metadata=meta
        )

    def postprocess(self, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model_name,
            "summary": raw_output["caption"],
            "confidence": raw_output["confidence"],
            "statistics": {
                "width": metadata["width"],
                "height": metadata["height"],
                "bands": metadata["bands"],
                "crs": metadata["crs"]
            },
            "evidence": {
                "caption": raw_output["caption"],
                "source_images": [raw_output["source_image"]]
            }
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "task": "captioning",
            "mode": self.mode
        }

    def get_capabilities(self):
        from app.ai.base import ModelCapability
        return ModelCapability(
            tasks=["captioning"],
            modalities=["optical"],
            input_formats=["raster"],
            output_formats=["text", "json"],
            min_inputs=1,
            max_inputs=1,
            supported_sensors=["Sentinel-2", "Landsat", "Aerial/Optical"],
            supports_gpu=True,
            supports_cpu=True
        )
