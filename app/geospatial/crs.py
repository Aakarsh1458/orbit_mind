from typing import Optional, Union
import pyproj
import rasterio.crs


def parse_crs(crs_input: Union[str, int, rasterio.crs.CRS, pyproj.CRS]) -> rasterio.crs.CRS:
    """
    Parses a CRS string, EPSG integer, or CRS object into a standard rasterio CRS.
    """
    if isinstance(crs_input, rasterio.crs.CRS):
        return crs_input
    if isinstance(crs_input, pyproj.CRS):
        return rasterio.crs.CRS.from_user_input(crs_input.to_wkt())
    if isinstance(crs_input, int):
        return rasterio.crs.CRS.from_epsg(crs_input)
    if isinstance(crs_input, str):
        crs_str = crs_input.strip()
        if crs_str.isdigit():
            return rasterio.crs.CRS.from_epsg(int(crs_str))
        return rasterio.crs.CRS.from_string(crs_str)

    return rasterio.crs.CRS.from_epsg(4326)


def are_crs_equal(
    crs_a: Union[str, rasterio.crs.CRS],
    crs_b: Union[str, rasterio.crs.CRS]
) -> bool:
    """
    Checks whether two CRSs are functionally equivalent.
    """
    try:
        parsed_a = parse_crs(crs_a)
        parsed_b = parse_crs(crs_b)
        return parsed_a == parsed_b
    except Exception:
        # String fallback comparison
        return str(crs_a).strip().upper() == str(crs_b).strip().upper()


def get_epsg_code(crs_input: Union[str, rasterio.crs.CRS]) -> Optional[int]:
    """
    Extracts EPSG code if available.
    """
    try:
        parsed = parse_crs(crs_input)
        return parsed.to_epsg()
    except Exception:
        return None
