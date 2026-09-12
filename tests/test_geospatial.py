import numpy as np
from pathlib import Path
from shapely.geometry import Polygon
from app.geospatial.raster import read_raster_metadata, read_bands, write_geotiff
from app.geospatial.crs import parse_crs, are_crs_equal, get_epsg_code
from app.geospatial.reprojection import check_spatial_overlap
from app.geospatial.vector import polygonize_mask, calculate_area_km2, bounds_to_geojson_polygon
from app.geospatial.statistics import calculate_change_statistics, calculate_segmentation_statistics


def test_raster_io_metadata(sample_geotiff_t1: str, tmp_path: Path):
    """Test reading raster metadata, reading bands, and writing a GeoTIFF."""
    meta = read_raster_metadata(sample_geotiff_t1)
    assert meta["width"] == 64
    assert meta["height"] == 64
    assert meta["bands"] == 3
    assert "EPSG:4326" in meta["crs"]
    assert meta["is_georeferenced"] is True

    bands = read_bands(sample_geotiff_t1)
    assert bands.shape == (3, 64, 64)

    # Write test
    out_tif = tmp_path / "written.tif"
    written_path = write_geotiff(
        output_path=out_tif,
        data=bands,
        transform=meta["transform"],
        crs=meta["crs"]
    )
    assert Path(written_path).exists()
    re_read_meta = read_raster_metadata(written_path)
    assert re_read_meta["width"] == 64


def test_crs_utilities():
    """Verify CRS parsing, equivalence, and EPSG extraction."""
    crs_4326 = parse_crs("EPSG:4326")
    assert crs_4326.to_epsg() == 4326

    assert are_crs_equal("EPSG:4326", 4326)
    assert are_crs_equal("EPSG:3857", "EPSG:3857")
    assert not are_crs_equal("EPSG:4326", "EPSG:3857")
    assert get_epsg_code("EPSG:4326") == 4326


def test_spatial_overlap():
    """Test bounding box overlap calculation."""
    bounds1 = {"left": 10.0, "bottom": 50.0, "right": 12.0, "top": 52.0}
    bounds2 = {"left": 11.0, "bottom": 51.0, "right": 13.0, "top": 53.0}
    bounds_disjoint = {"left": 20.0, "bottom": 60.0, "right": 22.0, "top": 62.0}

    assert check_spatial_overlap(bounds1, bounds2) is True
    assert check_spatial_overlap(bounds1, bounds_disjoint) is False


def test_vector_and_area():
    """Test polygonization of raster masks and geodesic area calculation."""
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 1

    transform = [0.001, 0.0, 10.0, 0.0, -0.001, 50.0]
    polygons = polygonize_mask(mask, transform=transform, crs="EPSG:4326")
    assert len(polygons) == 1

    area_km2 = calculate_area_km2(polygons[0], crs="EPSG:4326")
    assert area_km2 > 0.0


def test_change_and_segmentation_statistics():
    """Test change and segmentation summary statistics calculations."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[25:75, 25:75] = 1  # 2500 pixels changed out of 10,000

    stats = calculate_change_statistics(
        change_mask=mask,
        pixel_res_x=0.0001,
        pixel_res_y=0.0001,
        crs="EPSG:4326"
    )

    assert stats["total_pixels"] == 10000
    assert stats["changed_pixels"] == 2500
    assert stats["percentage_changed"] == 25.0
    assert stats["changed_area_km2"] > 0.0

    # Segmentation stats
    seg_mask = np.zeros((50, 50), dtype=np.uint8)
    seg_mask[:25, :] = 1  # water
    seg_mask[25:, :] = 2  # vegetation
    seg_stats = calculate_segmentation_statistics(
        seg_mask=seg_mask,
        class_mapping={1: "water", 2: "vegetation"},
        pixel_res_x=0.0001,
        pixel_res_y=0.0001
    )
    assert seg_stats["classes"]["water"]["pixels"] == 1250
    assert seg_stats["classes"]["vegetation"]["pixels"] == 1250
    assert "area_hectares" in seg_stats["classes"]["water"]
    assert "total_area_hectares" in seg_stats


def test_geodesic_metrics_and_hectares():
    """Verify geodesic area in km2 and hectares."""
    from app.geospatial.vector import calculate_area_hectares, calculate_geodesic_metrics
    poly = Polygon([(0.0, 0.0), (0.01, 0.0), (0.01, 0.01), (0.0, 0.01), (0.0, 0.0)])
    km2 = calculate_area_km2(poly, crs="EPSG:4326")
    hectares = calculate_area_hectares(poly, crs="EPSG:4326")
    metrics = calculate_geodesic_metrics(poly, crs="EPSG:4326")

    assert km2 > 0
    assert hectares == round(km2 * 100.0, 2)
    assert metrics["area_km2"] == round(km2, 4)
    assert metrics["area_hectares"] == hectares


async def test_tool_registry_whitelisted_tools(sample_geotiff_t1: str):
    """Verify whitelisted geospatial tool invocations via tool_registry."""
    from app.tools.registry import tool_registry
    from app.tools.schema import ToolCall

    # 1. read_metadata
    res_meta = await tool_registry.execute(
        ToolCall(tool="read_metadata", arguments={"file_path": sample_geotiff_t1})
    )
    assert res_meta.success is True
    assert res_meta.result["width"] == 64

    # 2. compute_geodesic_area
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [0.01, 0], [0.01, 0.01], [0, 0.01], [0, 0]]]}
    res_area = await tool_registry.execute(
        ToolCall(tool="compute_geodesic_area", arguments={"geometry": geom, "crs": "EPSG:4326"})
    )
    assert res_area.success is True
    assert "area_km2" in res_area.result
    assert "area_hectares" in res_area.result

    # 3. calculate_zonal_stats
    res_zonal = await tool_registry.execute(
        ToolCall(tool="calculate_zonal_stats", arguments={"raster_path": sample_geotiff_t1, "zones_path_or_geometry": geom})
    )
    assert res_zonal.success is True
    assert "mean" in res_zonal.result

