from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import rasterio.features
from rasterio.transform import Affine
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from shapely.ops import transform as shapely_transform
import pyproj

from app.core.logging import logger
from app.geospatial.crs import parse_crs


def bounds_to_geojson_polygon(bounds: Dict[str, float]) -> Dict[str, Any]:
    """
    Converts a bounding box dictionary into a GeoJSON Polygon.
    """
    left = bounds["left"]
    bottom = bounds["bottom"]
    right = bounds["right"]
    top = bounds["top"]

    polygon = Polygon([
        (left, bottom),
        (right, bottom),
        (right, top),
        (left, top),
        (left, bottom)
    ])
    return mapping(polygon)


def polygonize_mask(
    mask: np.ndarray,
    transform: Union[List[float], Affine],
    crs: str = "EPSG:4326",
    value_to_extract: int = 1,
    min_pixel_size: int = 4
) -> List[Dict[str, Any]]:
    """
    Converts raster mask regions with value_to_extract into vector GeoJSON polygons.
    """
    if isinstance(transform, list):
        affine_transform = Affine(*transform)
    else:
        affine_transform = transform

    # Ensure mask is 2D uint8 or int32
    if mask.ndim == 3:
        mask = mask[0]
    binary_mask = (mask == value_to_extract).astype(np.uint8)

    geometries = []
    for geom, val in rasterio.features.shapes(binary_mask, transform=affine_transform):
        if int(val) == 1:
            poly = shape(geom)
            if not poly.is_empty and poly.is_valid:
                geometries.append(mapping(poly))

    logger.info("Polygonized mask: extracted %d polygons", len(geometries))
    return geometries


def calculate_area_km2(
    geometry_or_geojson: Union[Dict[str, Any], Polygon, MultiPolygon],
    crs: str = "EPSG:4326"
) -> float:
    """
    Calculates geographic area of a geometry in square kilometers (km²).
    If CRS is geographic (EPSG:4326 / lat-lon), uses pyproj.Geod (WGS84 ellipsoid).
    If CRS is projected (e.g. UTM in meters), uses Cartesian area converted to km².
    """
    if isinstance(geometry_or_geojson, dict):
        poly = shape(geometry_or_geojson)
    else:
        poly = geometry_or_geojson

    if poly.is_empty:
        return 0.0

    parsed_crs = parse_crs(crs)

    if parsed_crs.is_geographic:
        # Use WGS84 Geodesic area
        geod = pyproj.Geod(ellps="WGS84")
        area_m2, _ = geod.geometry_area_perimeter(poly)
        return abs(area_m2) / 1_000_000.0
    else:
        # Projected in meters
        area_m2 = poly.area
        return abs(area_m2) / 1_000_000.0


def calculate_area_hectares(
    geometry_or_geojson: Union[Dict[str, Any], Polygon, MultiPolygon],
    crs: str = "EPSG:4326"
) -> float:
    """
    Calculates geographic area of a geometry in hectares (1 km² = 100 hectares).
    """
    return round(calculate_area_km2(geometry_or_geojson, crs=crs) * 100.0, 2)


def calculate_geodesic_metrics(
    geometry_or_geojson: Union[Dict[str, Any], Polygon, MultiPolygon],
    crs: str = "EPSG:4326"
) -> Dict[str, float]:
    """
    Calculates exact geodesic area in both km² and hectares using Shapely + PyProj.
    """
    km2 = calculate_area_km2(geometry_or_geojson, crs=crs)
    return {
        "area_km2": round(km2, 4),
        "area_hectares": round(km2 * 100.0, 2)
    }

