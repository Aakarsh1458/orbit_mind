from typing import Any, Dict, List, Optional
import numpy as np


def calculate_change_statistics(
    change_mask: np.ndarray,
    pixel_res_x: float,
    pixel_res_y: float,
    crs: str = "EPSG:4326"
) -> Dict[str, Any]:
    """
    Computes change statistics from a binary change mask (1 = changed, 0 = unchanged).
    """
    if change_mask.ndim == 3:
        mask_2d = change_mask[0]
    else:
        mask_2d = change_mask

    total_pixels = int(mask_2d.size)
    changed_pixels = int(np.sum(mask_2d > 0))
    unchanged_pixels = total_pixels - changed_pixels
    percentage_changed = (changed_pixels / total_pixels * 100.0) if total_pixels > 0 else 0.0

    # Area estimation based on pixel resolution
    # If in degrees (EPSG:4326), approximate at mid-latitude or convert via 111.32 km/deg
    if "4326" in str(crs):
        km_per_deg = 111.32
        pixel_area_km2 = (abs(pixel_res_x) * km_per_deg) * (abs(pixel_res_y) * km_per_deg)
    else:
        # Projected in meters: res is in meters
        pixel_area_km2 = (abs(pixel_res_x) * abs(pixel_res_y)) / 1_000_000.0

    changed_area_km2 = round(changed_pixels * pixel_area_km2, 4)
    total_area_km2 = round(total_pixels * pixel_area_km2, 4)

    return {
        "total_pixels": total_pixels,
        "changed_pixels": changed_pixels,
        "unchanged_pixels": unchanged_pixels,
        "percentage_changed": round(percentage_changed, 2),
        "changed_area_km2": changed_area_km2,
        "total_area_km2": total_area_km2,
        "changed_area_hectares": round(changed_area_km2 * 100.0, 2)
    }


def calculate_segmentation_statistics(
    seg_mask: np.ndarray,
    class_mapping: Dict[int, str],
    pixel_res_x: float,
    pixel_res_y: float,
    crs: str = "EPSG:4326"
) -> Dict[str, Any]:
    """
    Calculates pixel distributions, areas, and percentages for classified segmentation masks.
    """
    if seg_mask.ndim == 3:
        mask_2d = seg_mask[0]
    else:
        mask_2d = seg_mask

    total_pixels = int(mask_2d.size)

    if "4326" in str(crs):
        km_per_deg = 111.32
        pixel_area_km2 = (abs(pixel_res_x) * km_per_deg) * (abs(pixel_res_y) * km_per_deg)
    else:
        pixel_area_km2 = (abs(pixel_res_x) * abs(pixel_res_y)) / 1_000_000.0

    class_stats = {}
    for class_id, class_name in class_mapping.items():
        pixel_count = int(np.sum(mask_2d == class_id))
        area_km2 = round(pixel_count * pixel_area_km2, 4)
        pct = round((pixel_count / total_pixels * 100.0) if total_pixels > 0 else 0.0, 2)
        class_stats[class_name] = {
            "class_id": class_id,
            "pixels": pixel_count,
            "percentage": pct,
            "area_km2": area_km2
        }

    return {
        "total_pixels": total_pixels,
        "total_area_km2": round(total_pixels * pixel_area_km2, 4),
        "classes": class_stats
    }
