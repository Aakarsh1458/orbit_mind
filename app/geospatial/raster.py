import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.transform import Affine, from_origin
from PIL import Image

from app.core.logging import logger


def read_raster_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extracts comprehensive geospatial and image metadata from a raster file.
    Supports GeoTIFF, TIFF, and standard raster formats (PNG, JPEG).
    """
    path_str = str(file_path)
    suffix = Path(path_str).suffix.lower()

    # If it's a GeoTIFF / TIFF or readable by rasterio
    try:
        with rasterio.open(path_str) as src:
            crs_str = src.crs.to_string() if src.crs else "EPSG:4326"
            bounds = {
                "left": float(src.bounds.left),
                "bottom": float(src.bounds.bottom),
                "right": float(src.bounds.right),
                "top": float(src.bounds.top),
            }
            transform = list(src.transform)[:6]
            res = [float(abs(src.res[0])), float(abs(src.res[1]))]

            metadata = {
                "width": int(src.width),
                "height": int(src.height),
                "bands": int(src.count),
                "dtype": str(src.dtypes[0]),
                "nodata": float(src.nodata) if src.nodata is not None else None,
                "crs": crs_str,
                "transform": transform,
                "bounds": bounds,
                "resolution": res,
                "driver": src.driver,
                "is_georeferenced": src.crs is not None,
                "tags": dict(src.tags()),
            }
            return metadata
    except Exception as raster_err:
        logger.warning("Rasterio could not open %s directly (%s). Trying PIL fallback...", path_str, raster_err)

        # Fallback for standard images (PNG, JPG) without spatial metadata
        try:
            with Image.open(path_str) as img:
                width, height = img.size
                mode = img.mode
                bands = len(img.getbands())
                
                # Assign default spatial reference for testing purposes
                default_crs = "EPSG:4326"
                default_transform = [0.0001, 0.0, 0.0, 0.0, -0.0001, 0.0]
                bounds = {
                    "left": 0.0,
                    "bottom": -float(height * 0.0001),
                    "right": float(width * 0.0001),
                    "top": 0.0
                }

                return {
                    "width": width,
                    "height": height,
                    "bands": bands,
                    "dtype": "uint8",
                    "nodata": None,
                    "crs": default_crs,
                    "transform": default_transform,
                    "bounds": bounds,
                    "resolution": [0.0001, 0.0001],
                    "driver": suffix.upper().replace(".", ""),
                    "is_georeferenced": False,
                    "tags": {"mode": mode},
                }
        except Exception as pil_err:
            logger.error("Failed to read image metadata for %s: %s", path_str, pil_err)
            raise ValueError(f"Could not read metadata from raster file: {file_path}") from pil_err


def read_bands(
    file_path: Union[str, Path],
    bands: Optional[List[int]] = None
) -> np.ndarray:
    """
    Reads raster bands into a NumPy array with shape (bands, height, width).
    """
    path_str = str(file_path)
    try:
        with rasterio.open(path_str) as src:
            if bands:
                data = src.read(bands)
            else:
                data = src.read()
            return data
    except Exception:
        # Fallback using PIL
        with Image.open(path_str) as img:
            arr = np.array(img)
            if arr.ndim == 2:
                # (H, W) -> (1, H, W)
                return arr[np.newaxis, ...]
            elif arr.ndim == 3:
                # (H, W, C) -> (C, H, W)
                return np.transpose(arr, (2, 0, 1))
            return arr


def write_geotiff(
    output_path: Union[str, Path],
    data: np.ndarray,
    transform: Union[List[float], Affine],
    crs: Union[str, rasterio.crs.CRS] = "EPSG:4326",
    nodata: Optional[float] = None,
    dtype: Optional[str] = None
) -> str:
    """
    Writes a NumPy array to a valid GeoTIFF file preserving geospatial metadata.
    Accepts 2D array (height, width) or 3D array (bands, height, width).
    """
    out_path = Path(output_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if data.ndim == 2:
        count = 1
        height, width = data.shape
        data_to_write = data[np.newaxis, ...]
    elif data.ndim == 3:
        count, height, width = data.shape
        data_to_write = data
    else:
        raise ValueError(f"Unsupported array shape: {data.shape}. Expected 2D or 3D array.")

    # Format affine transform
    if isinstance(transform, list):
        affine_transform = Affine(*transform)
    else:
        affine_transform = transform

    # Determine dtype
    data_dtype = dtype or str(data.dtype)

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": count,
        "dtype": data_dtype,
        "crs": crs,
        "transform": affine_transform,
        "nodata": nodata,
        "compress": "deflate"
    }

    with rasterio.open(str(out_path), "w", **profile) as dst:
        dst.write(data_to_write.astype(data_dtype))

    logger.info("Successfully wrote GeoTIFF to %s (dims: %dx%d, bands: %d)", out_path, width, height, count)
    return str(out_path)
