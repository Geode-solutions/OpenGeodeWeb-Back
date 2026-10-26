from __future__ import annotations

# Standard library imports
import math
from typing import TYPE_CHECKING

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences

# Local application imports
from opengeodeweb_back.basemap.basemap_tiles import HALF_WORLD
from opengeodeweb_back.crs_functions import convert_xy_corners
from opengeodeweb_back.geode_objects.geode_triangulated_surface3d import (
    GeodeTriangulatedSurface3D,
)

if TYPE_CHECKING:
    from opengeodeweb_back.basemap.basemap_tiles import TileRange

GRID_SIZE = 32
UV_ATTRIBUTE = "basemap_uv"
WEB_MERCATOR = og_geosciences.GeographicCoordinateSystemInfo(
    "EPSG", "3857", "WGS 84 / Pseudo-Mercator"
)
OUTSIDE_MESSAGE = "Area outside the map projection limits"


class OutsideProjectionError(Exception):
    pass


def is_web_mercator(crs: og_geosciences.GeographicCoordinateSystemInfo) -> bool:
    return (crs.authority, crs.code) == (WEB_MERCATOR.authority, WEB_MERCATOR.code)


def bounds_to_3857(
    bounds: tuple[float, float, float, float],
    crs: og_geosciences.GeographicCoordinateSystemInfo,
) -> tuple[float, float, float, float]:
    """Bounding box in Web Mercator of the four corners of bounds, given in crs."""
    if is_web_mercator(crs):
        return _inside_web_mercator(bounds)
    try:
        corners = convert_xy_corners(bounds, crs, WEB_MERCATOR)
    except RuntimeError as error:  # PROJ rejects coordinates outside either CRS domain
        raise OutsideProjectionError(OUTSIDE_MESSAGE) from error
    xs = [x for x, _ in corners]
    ys = [y for _, y in corners]
    return _inside_web_mercator((min(xs), min(ys), max(xs), max(ys)))


def _inside_web_mercator(
    bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    if any(not abs(value) <= HALF_WORLD for value in bounds):  # also rejects NaN
        raise OutsideProjectionError(OUTSIDE_MESSAGE)
    return bounds


def build_mesh(
    tiles: TileRange,
    crs: og_geosciences.GeographicCoordinateSystemInfo,
    z_value: float,
    name: str,
) -> GeodeTriangulatedSurface3D:
    """Grid covering the tiles, with texture coordinates, converted from Web Mercator to crs."""
    x0, y0, x1, y1 = tiles.bounds_3857()
    mesh = GeodeTriangulatedSurface3D()
    builder = mesh.builder()
    builder.set_name(name)
    attributes = mesh.triangulated_surface.vertex_attribute_manager()
    values = og.AttributeValuesArrayDouble2()
    values.default_value = [0.0, 0.0]
    uv_id = attributes.create_attribute_variable_arraydouble2(
        UV_ATTRIBUTE, values, og.AttributeProperties()
    )
    uv = attributes.find_attribute_variable_arraydouble2(uv_id)
    last = GRID_SIZE - 1
    for row in range(GRID_SIZE):
        for column in range(GRID_SIZE):
            u, v = column / last, row / last
            point = og.Point3D([x0 + u * (x1 - x0), y0 + v * (y1 - y0), z_value])
            uv.set_value(builder.create_point(point), [u, v])
    for row in range(last):
        for column in range(last):
            corner = row * GRID_SIZE + column
            builder.create_triangle([corner, corner + 1, corner + GRID_SIZE + 1])
            builder.create_triangle([corner, corner + GRID_SIZE + 1, corner + GRID_SIZE])
    builder.compute_polygon_adjacencies()
    if is_web_mercator(crs):
        # Assigning then converting to the same CRS name is rejected by OpenGeode
        mesh.assign_crs(crs.authority_code(), crs)
        return mesh
    mesh.assign_crs(WEB_MERCATOR.authority_code(), WEB_MERCATOR)
    try:
        mesh.convert_crs(crs.authority_code(), crs)
    except RuntimeError as error:  # PROJ rejects tiles outside the project CRS domain
        raise OutsideProjectionError(OUTSIDE_MESSAGE) from error
    surface = mesh.triangulated_surface
    for vertex in range(surface.nb_vertices()):
        point = surface.point(vertex)
        if not all(math.isfinite(point.value(axis)) for axis in range(3)):
            raise OutsideProjectionError(OUTSIDE_MESSAGE)
    return mesh
