from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseRemoteSensingModel(ABC):
    """
    Common base interface for all remote sensing specialist models.
    Provides standard lifecycle hooks: loading, input validation, inference,
    postprocessing, and metadata discovery.
    """

    def __init__(self, mode: str = "mock"):
        self.mode = mode.lower()
        self.is_loaded = False

    @abstractmethod
    def load(self) -> None:
        """Loads weights, pipelines, or initializes mock engines."""
        pass

    @abstractmethod
    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """Validates that input imagery and parameters satisfy model requirements."""
        pass

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
