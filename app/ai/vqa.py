from pathlib import Path
from typing import Any, Dict, List
from app.ai.base import BaseRemoteSensingModel
from app.core.logging import logger
from app.geospatial.raster import read_raster_metadata


class VQAModel(BaseRemoteSensingModel):
    """
    Visual Question Answering specialist model for satellite imagery.
    Answers natural-language questions concerning imagery features, presence of infrastructure,
    or geographic attributes.
    """

    def __init__(self, mode: str = "mock"):
        super().__init__(mode=mode)
        self.model_name = "OrbitMind-RemoteSensing-VQA-v1"

    def load(self) -> None:
        if self.mode == "production":
            logger.info("Production mode: Initializing Multimodal Visual Question Answering pipeline...")
            self.is_loaded = True
        else:
            logger.info("Mock mode: Initializing semantic question parsing engine.")
            self.is_loaded = True

    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        if not inputs.get("query"):
            raise ValueError("VQA requires a non-empty question / query.")
        imagery_paths = inputs.get("imagery_paths", [])
        if not imagery_paths:
            raise ValueError("VQA requires at least one satellite image input.")
        if not Path(imagery_paths[0]).exists():
            raise FileNotFoundError(f"Input image not found: {imagery_paths[0]}")
        return True

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self.validate_input(inputs)
        query = inputs["query"].strip().lower()
        img_path = Path(inputs["imagery_paths"][0])
        meta = read_raster_metadata(img_path)

        if self.mode == "production":
            raise NotImplementedError(
                "Production VQA model checkpoint not configured. "
                "Specify model weights in MODEL_CACHE_DIR or run in AI_MODE=mock."
            )
        else:
            # Deterministic domain-specific VQA reasoning
            confidence = 0.86
            if any(w in query for w in ["water", "river", "lake", "ocean", "flood"]):
                answer = "Water bodies are prominently visible in the southern and eastern quadrants of the scene."
            elif any(w in query for w in ["urban", "building", "city", "structure", "housing"]):
                answer = "Dense urban clusters and residential infrastructure are detected in the central sector."
            elif any(w in query for w in ["vegetation", "forest", "tree", "agriculture", "crop"]):
                answer = "Substantial agricultural and forested canopy is present across northern parcels."
            elif any(w in query for w in ["road", "highway", "transit", "infrastructure"]):
                answer = "Major arterial roads and transportation networks traverse horizontally through the area."
            elif any(w in query for w in ["how many", "count", "number"]):
                answer = "Approximately 4 primary distinct geographic zones and multiple structural clusters are identified."
            else:
                answer = (
                    f"Analysis of {meta['width']}x{meta['height']} satellite acquisition "
                    f"indicates mixed land use with balanced natural canopy and developed terrain."
                )

        return self.postprocess(
            raw_output={
                "answer": answer,
                "confidence": confidence,
                "query": inputs["query"],
                "source_image": str(img_path)
            },
            metadata=meta
        )

    def postprocess(self, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model_name,
            "summary": raw_output["answer"],
            "confidence": raw_output["confidence"],
            "statistics": {
                "imagery_dimensions": f"{metadata['width']}x{metadata['height']}",
                "bands_analyzed": metadata["bands"],
                "crs": metadata["crs"]
            },
            "evidence": {
                "question": raw_output["query"],
                "answer": raw_output["answer"],
                "source_images": [raw_output["source_image"]]
            }
        }

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "task": "vqa",
            "mode": self.mode,
            "modality": "Vision-Language"
        }
