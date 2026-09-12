from typing import Any, Dict
from app.geospatial.statistics import calculate_change_statistics, calculate_segmentation_statistics


class StatisticsService:
    """Service wrapping spatial metric computation and geodesic unit harmonization."""

    def format_statistics(self, raw_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures consistent structure for statistical metadata, guaranteeing km² and hectares."""
        stats = dict(raw_stats)

        # Harmonize change statistics
        if "changed_area_km2" in stats and "changed_area_hectares" not in stats:
            stats["changed_area_hectares"] = round(stats["changed_area_km2"] * 100.0, 2)
        elif "changed_area_hectares" in stats and "changed_area_km2" not in stats:
            stats["changed_area_km2"] = round(stats["changed_area_hectares"] / 100.0, 4)

        if "total_area_km2" in stats and "total_area_hectares" not in stats:
            stats["total_area_hectares"] = round(stats["total_area_km2"] * 100.0, 2)

        if "area_km2" in stats and "area_hectares" not in stats:
            stats["area_hectares"] = round(stats["area_km2"] * 100.0, 2)

        # Harmonize class-level segmentation metrics
        if "classes" in stats and isinstance(stats["classes"], dict):
            for cls_name, cls_info in stats["classes"].items():
                if isinstance(cls_info, dict) and "area_km2" in cls_info and "area_hectares" not in cls_info:
                    cls_info["area_hectares"] = round(cls_info["area_km2"] * 100.0, 2)

        return stats


statistics_service = StatisticsService()
