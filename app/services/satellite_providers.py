from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from app.core.logging import logger
from app.geospatial.raster import read_raster_metadata


class SatelliteDataProvider(ABC):
    """
    Abstract interface for satellite data providers (Sentinel-1, Sentinel-2, Landsat, Local files).
    Enables future plug-and-play integrations with STAC APIs, Copernicus, Planetary Computer.
    """

    @abstractmethod
    def search(self, bbox: List[float], time_range: Optional[Union[Tuple[Any, ...], List[Any]]] = None, **kwargs) -> List[Dict[str, Any]]:
        """Search catalog for matching satellite acquisitions."""
        pass

    @abstractmethod
    def get_metadata(self, identifier: str) -> Dict[str, Any]:
        """Fetch provider metadata for a given scene or asset."""
        pass

    @abstractmethod
    def download_or_load(self, identifier: str, output_path: Optional[Union[str, Path]] = None) -> str:
        """Fetch or load imagery file into local filesystem."""
        pass


class LocalFileProvider(SatelliteDataProvider):
    """
    Local filesystem provider for user-uploaded satellite imagery.
    """

    def __init__(self, base_dir: Union[str, Path] = "./data/uploads"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def search(self, bbox: Optional[List[float]] = None, time_range: Optional[Any] = None, **kwargs) -> List[Dict[str, Any]]:
        results = []
        for file in self.base_dir.glob("*.tif*"):
            try:
                meta = read_raster_metadata(file)
                results.append({"id": file.name, "path": str(file), "metadata": meta})
            except Exception as e:
                logger.warning("Error inspecting local file %s: %s", file, e)
        return results

    def get_metadata(self, identifier: str) -> Dict[str, Any]:
        path = self.base_dir / identifier
        if not path.exists():
            raise FileNotFoundError(f"Local file {identifier} does not exist in {self.base_dir}")
        return read_raster_metadata(path)

    def download_or_load(self, identifier: str, output_path: Optional[Union[str, Path]] = None) -> str:
        path = self.base_dir / identifier
        if not path.exists():
            raise FileNotFoundError(f"Local file {identifier} not found.")
        return str(path)


class SentinelProvider(SatelliteDataProvider):
    """
    Extensible connector for Copernicus / Sentinel-1 (SAR) & Sentinel-2 (Optical).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, bbox: List[float], time_range: Any, **kwargs) -> List[Dict[str, Any]]:
        logger.info("SentinelProvider search called with bbox %s. Extensible connector ready.", bbox)
        return []

    def get_metadata(self, identifier: str) -> Dict[str, Any]:
        return {
            "provider": "Copernicus/Sentinel",
            "identifier": identifier,
            "status": "configured"
        }

    def download_or_load(self, identifier: str, output_path: Optional[Union[str, Path]] = None) -> str:
        raise NotImplementedError("Direct Sentinel download requires remote STAC credentials.")


class LandsatProvider(SatelliteDataProvider):
    """
    Extensible connector for USGS / Landsat optical missions.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def search(self, bbox: List[float], time_range: Any, **kwargs) -> List[Dict[str, Any]]:
        logger.info("LandsatProvider search called with bbox %s. Extensible connector ready.", bbox)
        return []

    def get_metadata(self, identifier: str) -> Dict[str, Any]:
        return {
            "provider": "USGS/Landsat",
            "identifier": identifier,
            "status": "configured"
        }

    def download_or_load(self, identifier: str, output_path: Optional[Union[str, Path]] = None) -> str:
        raise NotImplementedError("Direct Landsat download requires USGS STAC credentials.")
