from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelCapability(BaseModel):
    """Declarative capability profile for remote sensing models."""
    tasks: List[str] = Field(..., description="List of tasks e.g. ['change_detection']")
    modalities: List[str] = Field(default_factory=lambda: ["optical"], description="e.g. ['optical', 'sar']")
    input_formats: List[str] = Field(default_factory=lambda: ["raster", "geotiff"])
    output_formats: List[str] = Field(default_factory=lambda: ["probability_mask", "geotiff"])
    min_inputs: int = 1
    max_inputs: int = 2
    supported_sensors: List[str] = Field(default_factory=lambda: ["Sentinel-2", "Landsat", "Aerial"])
    supports_gpu: bool = True
    supports_cpu: bool = True


class ModelUnavailableError(Exception):
    """
    Raised when specialist model weights or GPU inference engines are unavailable
    in production mode. Carries an explicit status_code: 'MODEL_UNAVAILABLE'.
    """
    def __init__(self, message: str, status_code: str = "MODEL_UNAVAILABLE"):
        super().__init__(message)
        self.status_code = status_code
        self.message = message



class BaseRemoteSensingModel(ABC):
    """
    Common base interface for all remote sensing specialist models and AI engines.
    Provides standard lifecycle hooks: loading, input validation, preprocessing,
    inference, postprocessing, metadata, and capability discovery.
    """

    def __init__(self, mode: str = "mock"):
        self.mode = mode.lower()
        self.is_loaded = False

    @abstractmethod
    def load(self) -> None:
        """Loads model weights or initializes inference engine."""
        pass

    @abstractmethod
    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """Validates that input imagery and parameters satisfy model requirements."""
        pass

    def preprocess(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Optional model-specific preprocessing hook."""
        return inputs

    @abstractmethod
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Executes inference on validated inputs."""
        pass

    @abstractmethod
    def postprocess(self, raw_output: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Formats model output into structured evidence, statistics, and answers."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns model architecture, version, task name, and mode information."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ModelCapability:
        """Returns declarative capability profile."""
        pass


BaseAIEngine = BaseRemoteSensingModel
