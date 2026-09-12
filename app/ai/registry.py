from typing import Any, Dict, List, Optional, Type
from app.ai.base import BaseRemoteSensingModel, ModelCapability
from app.ai.vqa import VQAModel
from app.ai.captioning import CaptioningModel
from app.ai.change_detection import ChangeDetectionModel, BaselineChangeDetectionFallback
from app.ai.segmentation import SegmentationModel
from app.ai.optical_sar import OpticalSARModel
from app.ai.cloud_removal import CloudRemovalModel
from app.core.config import settings
from app.core.logging import logger


class ModelRegistry:
    """
    Registry for OrbitMind specialist remote sensing models.
    Supports dynamic lookup, fallback routing, and capability inspection.
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseRemoteSensingModel]] = {
            "vqa": VQAModel,
            "captioning": CaptioningModel,
            "change_detection": ChangeDetectionModel,
            "segmentation": SegmentationModel,
            "optical_sar": OpticalSARModel,
            "cloud_removal": CloudRemovalModel,
        }
        self._fallbacks: Dict[str, Type[BaseRemoteSensingModel]] = {
            "change_detection": BaselineChangeDetectionFallback,
            "segmentation": SegmentationModel,  # fallback with standard spectral thresholds
            "captioning": CaptioningModel,
            "vqa": VQAModel,
            "optical_sar": OpticalSARModel,
            "cloud_removal": CloudRemovalModel,
        }

    def register(
        self,
        task_name: str,
        model_cls: Type[BaseRemoteSensingModel],
        fallback_cls: Optional[Type[BaseRemoteSensingModel]] = None
    ) -> None:
        key = task_name.lower().strip()
        self._registry[key] = model_cls
        if fallback_cls:
            self._fallbacks[key] = fallback_cls
        logger.info("Registered model %s for task '%s'", model_cls.__name__, key)

    def get_model(self, task_name: str, mode: Optional[str] = None) -> BaseRemoteSensingModel:
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

    def get_fallback_model(self, task_name: str, mode: Optional[str] = None) -> Optional[BaseRemoteSensingModel]:
        key = task_name.lower().strip()
        fallback_cls = self._fallbacks.get(key)
        if not fallback_cls:
            return None
        target_mode = (mode or settings.AI_MODE).lower()
        instance = fallback_cls(mode=target_mode)
        instance.load()
        return instance

    def get_capabilities(self, task_name: str) -> Optional[ModelCapability]:
        key = task_name.lower().strip()
        if key not in self._registry:
            return None
        model_cls = self._registry[key]
        temp_inst = model_cls(mode="mock")
        return temp_inst.get_capabilities()

    def list_available_models(self) -> Dict[str, str]:
        return {k: v.__name__ for k, v in self._registry.items()}

    def list_model_details(self) -> List[Dict[str, Any]]:
        details = []
        for task, cls_ref in self._registry.items():
            temp = cls_ref(mode="mock")
            caps = temp.get_capabilities().model_dump()
            meta = temp.get_metadata()
            details.append({
                "task": task,
                "model_name": meta.get("name", cls_ref.__name__),
                "primary_class": cls_ref.__name__,
                "fallback_available": task in self._fallbacks,
                "capabilities": caps
            })
        return details


model_registry = ModelRegistry()
