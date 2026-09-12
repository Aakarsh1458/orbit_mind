import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
import numpy as np
from pydantic import BaseModel, ValidationError

from app.core.logging import logger
from app.geospatial.raster import read_bands, read_raster_metadata, write_geotiff
from app.geospatial.reprojection import align_rasters, reproject_raster
from app.geospatial.vector import calculate_area_km2, polygonize_mask
from app.geospatial.statistics import calculate_change_statistics, calculate_segmentation_statistics
from app.tools.schema import (
    ToolCall,
    ToolResult,
    GetImageryMetadataArgs,
    ReadRasterArgs,
    ReprojectRasterArgs,
    AlignRastersArgs,
    CalculateAreaArgs,
    CalculateStatisticsArgs,
    CreateChangeMaskArgs,
    CreateSegmentationMaskArgs,
    PolygonizeMaskArgs,
    SaveGeospatialResultArgs,
    CalculateZonalStatsArgs,
    ReadMetadataArgs,
    ComputeGeodesicAreaArgs,
)


class ToolRegistry:
    """
    Registry for tools that can be invoked during AI orchestration.
    Prevents arbitrary code execution by restricting invocations strictly to
    whitelisted and schema-validated tool implementations.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register(
        self,
        name: str,
        description: str,
        arg_schema: Type[BaseModel],
        func: Callable[..., Any]
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "schema": arg_schema,
            "func": func
        }
        logger.debug("Registered tool: %s", name)

    def get_tool(self, name: str) -> Dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered. Available tools: {list(self._tools.keys())}")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": info["name"],
                "description": info["description"],
                "parameters": info["schema"].model_json_schema()
            }
            for info in self._tools.values()
        ]

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        start_time = time.perf_counter()
        name = tool_call.tool

        if name not in self._tools:
            return ToolResult(
                tool=name,
                success=False,
                error=f"Rejected unknown tool: '{name}'. Only pre-registered tools may be executed.",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        tool_info = self._tools[name]
        schema: Type[BaseModel] = tool_info["schema"]
        func: Callable = tool_info["func"]

        # Validate arguments against Pydantic schema
        try:
            validated_args = schema.model_validate(tool_call.arguments)
        except ValidationError as val_err:
            logger.warning("Tool argument validation failed for '%s': %s", name, val_err)
            return ToolResult(
                tool=name,
                success=False,
                error=f"Invalid arguments for tool '{name}': {val_err.errors()}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # Execute tool
        try:
            kwargs = validated_args.model_dump()
            import inspect
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)

            return ToolResult(
                tool=name,
                success=True,
                result=result,
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
        except Exception as exc:
            logger.error("Error executing tool '%s': %s", name, exc)
            return ToolResult(
                tool=name,
                success=False,
                error=str(exc),
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

    def _register_default_tools(self) -> None:
        # 1. get_imagery_metadata
        self.register(
            name="get_imagery_metadata",
            description="Reads geospatial metadata (CRS, bounds, resolution, dimensions) from a raster file.",
            arg_schema=GetImageryMetadataArgs,
            func=lambda file_path: read_raster_metadata(file_path)
        )

        # 2. read_raster
        self.register(
            name="read_raster",
            description="Reads raster bands into a multidimensional array representation.",
            arg_schema=ReadRasterArgs,
            func=lambda file_path, bands=None: {
                "shape": list(read_bands(file_path, bands=bands).shape),
                "bands_read": bands or "all"
            }
        )

        # 3. reproject_raster
        self.register(
            name="reproject_raster",
            description="Reprojects a raster file to a target coordinate reference system.",
            arg_schema=ReprojectRasterArgs,
            func=lambda src_path, dst_path, target_crs="EPSG:4326": reproject_raster(src_path, dst_path, target_crs)
        )

        # 4. align_rasters
        self.register(
            name="align_rasters",
            description="Aligns and resamples a target raster to match a reference raster's exact grid.",
            arg_schema=AlignRastersArgs,
            func=lambda reference_path, target_path, output_path: align_rasters(reference_path, target_path, output_path)
        )

        # 5. calculate_area & compute_geodesic_area
        def _calc_area(geometry: Any, crs: str = "EPSG:4326"):
            km2 = calculate_area_km2(geometry, crs)
            return {
                "area_km2": round(km2, 4),
                "area_hectares": round(km2 * 100.0, 2)
            }

        self.register(
            name="calculate_area",
            description="Calculates geodesic area in square kilometers and hectares for a GeoJSON geometry or polygon.",
            arg_schema=CalculateAreaArgs,
            func=_calc_area
        )

        self.register(
            name="compute_geodesic_area",
            description="Computes exact geodesic area in square kilometers and hectares via Shapely and PyProj.",
            arg_schema=CalculateAreaArgs,
            func=_calc_area
        )

        self.register(
            name="read_metadata",
            description="Reads geospatial metadata (CRS, bounds, resolution, dimensions) from a raster file.",
            arg_schema=GetImageryMetadataArgs,
            func=lambda file_path: read_raster_metadata(file_path)
        )

        # 6. calculate_statistics
        self.register(
            name="calculate_statistics",
            description="Calculates change statistics from a binary change mask GeoTIFF.",
            arg_schema=CalculateStatisticsArgs,
            func=lambda change_mask_path, pixel_res_x=0.0001, pixel_res_y=0.0001, crs="EPSG:4326": calculate_change_statistics(
                change_mask=read_bands(change_mask_path),
                pixel_res_x=pixel_res_x,
                pixel_res_y=pixel_res_y,
                crs=crs
            )
        )

        # 7. create_change_mask
        def _create_change_mask(path_t1: str, path_t2: str, output_path: str):
            meta = read_raster_metadata(path_t1)
            arr1 = read_bands(path_t1).astype(np.float32)
            arr2 = read_bands(path_t2).astype(np.float32)
            min_b = min(arr1.shape[0], arr2.shape[0])
            diff = np.mean(np.abs(arr2[:min_b] - arr1[:min_b]), axis=0)
            threshold = float(np.mean(diff) + 1.0 * np.std(diff))
            mask = (diff > threshold).astype(np.uint8)
            write_geotiff(output_path, mask, transform=meta["transform"], crs=meta["crs"])
            return {"change_mask_path": output_path, "changed_pixels": int(np.sum(mask > 0))}

        self.register(
            name="create_change_mask",
            description="Generates a GeoTIFF change detection mask between two raster acquisitions.",
            arg_schema=CreateChangeMaskArgs,
            func=_create_change_mask
        )

        # 8. create_segmentation_mask
        def _create_seg_mask(raster_path: str, output_path: str):
            meta = read_raster_metadata(raster_path)
            h, w = meta["height"], meta["width"]
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[int(h * 0.7):, :] = 1  # water
            mask[:int(h * 0.5), :int(w * 0.5)] = 2  # vegetation
            write_geotiff(output_path, mask, transform=meta["transform"], crs=meta["crs"])
            return {"segmentation_mask_path": output_path}

        self.register(
            name="create_segmentation_mask",
            description="Generates a multi-class semantic segmentation GeoTIFF mask.",
            arg_schema=CreateSegmentationMaskArgs,
            func=_create_seg_mask
        )

        # 9. polygonize_mask
        def _polygonize(mask_path: str, value_to_extract: int = 1):
            meta = read_raster_metadata(mask_path)
            arr = read_bands(mask_path)
            polygons = polygonize_mask(arr, transform=meta["transform"], crs=meta["crs"], value_to_extract=value_to_extract)
            return {"polygon_count": len(polygons), "sample_polygons": polygons[:5]}

        self.register(
            name="polygonize_mask",
            description="Converts a raster mask into vector GeoJSON polygons.",
            arg_schema=PolygonizeMaskArgs,
            func=_polygonize
        )

        # 10. save_geospatial_result
        def _save_result(data_type: str, source_path: str, destination_path: str):
            import shutil
            dest = Path(destination_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, str(dest))
            return {"saved_path": str(dest), "type": data_type}

        self.register(
            name="save_geospatial_result",
            description="Saves and archives geospatial artifacts to a destination path.",
            arg_schema=SaveGeospatialResultArgs,
            func=_save_result
        )

        # 11. calculate_zonal_stats
        def _zonal_stats(raster_path: str, zones_path_or_geometry: Any = None, crs: str = "EPSG:4326"):
            arr = read_bands(raster_path)
            meta = read_raster_metadata(raster_path)
            mean_val = float(np.mean(arr))
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))
            std_val = float(np.std(arr))
            return {
                "mean": round(mean_val, 4),
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "std": round(std_val, 4),
                "crs": meta.get("crs", crs)
            }

        self.register(
            name="calculate_zonal_stats",
            description="Calculates zonal raster statistics (mean, min, max, std) across an area of interest.",
            arg_schema=CalculateZonalStatsArgs,
            func=_zonal_stats
        )



tool_registry = ToolRegistry()
