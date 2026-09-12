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


def read_raster(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Reads both metadata and data array for a raster."""
    metadata = read_raster_metadata(file_path)
    data = read_bands(file_path)
    return {
        "data": data,
        "metadata": metadata,
        "crs": metadata.get("crs", "EPSG:4326"),
        "transform": metadata.get("transform")
    }


def write_raster(
    output_path: Union[str, Path],
    data: np.ndarray,
    crs: Union[str, rasterio.crs.CRS] = "EPSG:4326",
    transform: Optional[Union[List[float], Affine]] = None
) -> str:
    """Convenience function around write_geotiff."""
    t = transform or [0.0001, 0.0, 0.0, 0.0, -0.0001, 0.0]
    return write_geotiff(output_path=output_path, data=data, transform=t, crs=crs)


def generate_raster_preview_bytes(file_path: Union[str, Path]) -> bytes:
    """
    Converts any geospatial raster (GeoTIFF, TIFF, SAR, multispectral)
    into standard web-compatible PNG image bytes with 2-98% contrast stretch.
    """
    import io
    path = Path(file_path).resolve()
    suffix = path.suffix.lower()

    if suffix in (".png", ".jpg", ".jpeg", ".webp"):
        return path.read_bytes()

    try:
        with rasterio.open(str(path)) as src:
            count = src.count
            if count >= 3:
                # If Sentinel-2 / Landsat with 4+ bands, use Red, Green, Blue (typically 4, 3, 2)
                bands = [4, 3, 2] if count >= 4 else [1, 2, 3]
                data = src.read(bands).astype(np.float32)
                rgb = np.zeros((data.shape[1], data.shape[2], 3), dtype=np.uint8)
                for i in range(3):
                    b = data[i]
                    p2, p98 = np.percentile(b, (2, 98))
                    if p98 > p2:
                        b_norm = np.clip((b - p2) / (p98 - p2), 0, 1) * 255.0
                    else:
                        b_norm = np.clip(b, 0, 255)
                    rgb[:, :, i] = b_norm.astype(np.uint8)
                img = Image.fromarray(rgb)
            elif count == 2:
                # SAR polarizations (e.g. VV and VH)
                data = src.read().astype(np.float32)
                vv, vh = data[0], data[1]
                p2_vv, p98_vv = np.percentile(vv, (2, 98))
                p2_vh, p98_vh = np.percentile(vh, (2, 98))
                norm_vv = np.clip((vv - p2_vv) / (max(p98_vv - p2_vv, 1e-4)), 0, 1) * 255.0
                norm_vh = np.clip((vh - p2_vh) / (max(p98_vh - p2_vh, 1e-4)), 0, 1) * 255.0
                ratio = np.clip((norm_vv / (norm_vh + 1.0)) * 128.0, 0, 255)
                rgb = np.stack([norm_vv.astype(np.uint8), norm_vh.astype(np.uint8), ratio.astype(np.uint8)], axis=-1)
                img = Image.fromarray(rgb)
            else:
                b = src.read(1).astype(np.float32)
                p2, p98 = np.percentile(b, (2, 98))
                if p98 > p2:
                    b_norm = np.clip((b - p2) / (p98 - p2), 0, 1) * 255.0
                else:
                    b_norm = np.clip(b, 0, 255)
                img = Image.fromarray(b_norm.astype(np.uint8))

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
    except Exception as e:
        logger.warning("Rasterio preview generation failed for %s (%s). Falling back to PIL.", path, e)
        with Image.open(str(path)) as pil_img:
            buf = io.BytesIO()
            pil_img.convert("RGB").save(buf, format="PNG")
            return buf.getvalue()


def get_or_create_preview_file(file_path: Union[str, Path]) -> Path:
    """
    Returns a Path to a browser-renderable image file (PNG).
    Caches converted GeoTIFFs to disk next to the original file as *_preview.png.
    """
    path = Path(file_path).resolve()
    if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
        return path

    cache_path = path.parent / f"{path.stem}_preview.png"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        if cache_path.stat().st_mtime >= path.stat().st_mtime:
            return cache_path

    # Generate and write cache
    png_bytes = generate_raster_preview_bytes(path)
    with open(cache_path, "wb") as f:
        f.write(png_bytes)
    return cache_path


