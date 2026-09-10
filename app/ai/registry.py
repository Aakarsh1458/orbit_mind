from typing import Dict, Type
from app.ai.base import BaseRemoteSensingModel
from app.ai.vqa import VQAModel
from app.ai.captioning import CaptioningModel
from app.ai.change_detection import ChangeDetectionModel
from app.ai.segmentation import SegmentationModel
from app.ai.optical_sar import OpticalSARModel
from app.core.config import settings
from app.core.logging import logger


class ModelRegistry:
    """
    Registry for OrbitMind specialist remote sensing models.
    Supports dynamic lookup, factory instantiation, and model listing.
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseRemoteSensingModel]] = {
            "vqa": VQAModel,
            "captioning": CaptioningModel,
            "change_detection": ChangeDetectionModel,
            "segmentation": SegmentationModel,
            "optical_sar": OpticalSARModel
        }

    def register(self, task_name: str, model_cls: Type[BaseRemoteSensingModel]) -> None:
        key = task_name.lower().strip()
        self._registry[key] = model_cls
        logger.info("Registered model class %s for task '%s'", model_cls.__name__, key)

    def get_model(self, task_name: str, mode: str = None) -> BaseRemoteSensingModel:
        key = task_name.lower().strip()
        if key not in self._registry:
            raise KeyError(
                f"Unknown model task: '{task_name}'. Available models: {list(self._registry.keys())}"
            )

        target_mode = (mode or settings.AI_MODE).lower()
        model_cls = self._registry[key]
        instance = model_cls(mode=target_mode)
        instance.load()
        return instance

    def list_available_models(self) -> Dict[str, str]:
        return {k: v.__name__ for k, v in self._registry.items()}


# Global model registry instance
model_registry = ModelRegistry()
