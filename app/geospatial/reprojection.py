from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import Affine

from app.core.logging import logger
from app.geospatial.crs import are_crs_equal, parse_crs


def check_spatial_overlap(
    bounds_a: Dict[str, float],
    bounds_b: Dict[str, float]
) -> bool:
    """
    Checks whether two bounding boxes overlap in space.
    bounds format: {"left": ..., "bottom": ..., "right": ..., "top": ...}
    """
    overlap_x = max(bounds_a["left"], bounds_b["left"]) < min(bounds_a["right"], bounds_b["right"])
    overlap_y = max(bounds_a["bottom"], bounds_b["bottom"]) < min(bounds_a["top"], bounds_b["top"])
    return overlap_x and overlap_y


def reproject_raster(
    src_path: Union[str, Path],
    dst_path: Union[str, Path],
    target_crs: Union[str, rasterio.crs.CRS] = "EPSG:4326",
    resampling: Resampling = Resampling.bilinear
) -> str:
    """
    Reprojects a raster to a target Coordinate Reference System.
    """
    src_p = Path(src_path).resolve()
    dst_p = Path(dst_path).resolve()
    dst_p.parent.mkdir(parents=True, exist_ok=True)

    dst_crs = parse_crs(target_crs)

    with rasterio.open(str(src_p)) as src:
        src_crs = src.crs or parse_crs("EPSG:4326")

        if are_crs_equal(src_crs, dst_crs):
            logger.info("Source CRS equals target CRS. Direct copy or passthrough.")

        transform, width, height = calculate_default_transform(
            src_crs, dst_crs, src.width, src.height, *src.bounds
        )

        profile = src.profile.copy()
        profile.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "driver": "GTiff",
            "compress": "deflate"
        })

        with rasterio.open(str(dst_p), "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling
                )

    logger.info("Successfully reprojected %s to %s with CRS %s", src_p.name, dst_p.name, dst_crs)
    return str(dst_p)


def align_rasters(
    reference_path: Union[str, Path],
    target_path: Union[str, Path],
    output_path: Union[str, Path],
    resampling: Resampling = Resampling.bilinear
) -> str:
    """
    Reprojects and resamples target raster so that its grid, CRS, dimensions,
    and transform exactly match the reference raster.
    """
    ref_p = Path(reference_path).resolve()
    tgt_p = Path(target_path).resolve()
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(str(ref_p)) as ref:
        ref_crs = ref.crs or parse_crs("EPSG:4326")
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height
        ref_profile = ref.profile.copy()

        with rasterio.open(str(tgt_p)) as tgt:
            tgt_crs = tgt.crs or parse_crs("EPSG:4326")

            # Configure output profile matching reference grid
            out_profile = tgt.profile.copy()
            out_profile.update({
                "crs": ref_crs,
                "transform": ref_transform,
                "width": ref_width,
                "height": ref_height,
                "driver": "GTiff",
                "compress": "deflate"
            })

            with rasterio.open(str(out_p), "w", **out_profile) as dst:
                for i in range(1, tgt.count + 1):
                    reproject(
                        source=rasterio.band(tgt, i),
                        destination=rasterio.band(dst, i),
                        src_transform=tgt.transform,
                        src_crs=tgt_crs,
                        dst_transform=ref_transform,
                        dst_crs=ref_crs,
                        resampling=resampling
                    )

    logger.info("Successfully aligned %s to match reference %s at %s", tgt_p.name, ref_p.name, out_p.name)
    return str(out_p)
