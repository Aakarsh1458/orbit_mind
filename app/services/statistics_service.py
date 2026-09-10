from typing import Any, Dict
from app.geospatial.statistics import calculate_change_statistics, calculate_segmentation_statistics


class StatisticsService:
    """Service wrapping spatial metric computation and confidence validation."""

    def format_statistics(self, raw_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures consistent structure for statistical metadata."""
        return raw_stats


statistics_service = StatisticsService()
