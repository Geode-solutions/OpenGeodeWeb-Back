from __future__ import annotations

# Standard library imports
import contextlib
import functools
import logging
import math
import os
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences

# Local application imports
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep
from opengeodeweb_back.geode_objects.geode_edged_curve2d import GeodeEdgedCurve2D
from opengeodeweb_back.geode_objects.geode_edged_curve3d import GeodeEdgedCurve3D
from opengeodeweb_back.geode_objects.geode_point_set2d import GeodePointSet2D
from opengeodeweb_back.geode_objects.geode_point_set3d import GeodePointSet3D
from opengeodeweb_back.geode_objects.geode_section import GeodeSection
from opengeodeweb_back.geode_objects.geode_solid_mesh3d import GeodeSolidMesh3D
from opengeodeweb_back.geode_objects.geode_surface_mesh2d import GeodeSurfaceMesh2D
from opengeodeweb_back.geode_objects.geode_surface_mesh3d import GeodeSurfaceMesh3D

if TYPE_CHECKING:
    from opengeodeweb_back.geode_objects.crs_coordinates import Mesh
    from opengeodeweb_back.geode_objects.geode_object import GeodeObject

logger = logging.getLogger(__name__)

ORIGINAL_CRS = "points"
# OpenGeode orders EPSG:4326 coordinates as (latitude, longitude)
WGS84 = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "4326", "WGS 84")
MAX_LATITUDE = 90.0
MAX_LONGITUDE = 180.0

# TEMPORARY workaround, to remove once OpenGeode sets it itself (and ships a PyInstaller hook):
# PROJ looks for its database next to the loaded libproj, which packaged apps (PyInstaller)
# Load from elsewhere, so point it to the one opengeode ships
os.environ.setdefault("PROJ_DATA", str(Path(og.__file__).parent / "share" / "proj"))

CRS_GEODE_OBJECTS = (
    GeodeBRep,
    GeodeSection,
    GeodePointSet2D,
    GeodePointSet3D,
    GeodeEdgedCurve2D,
    GeodeEdgedCurve3D,
    GeodeSurfaceMesh2D,
    GeodeSurfaceMesh3D,
    GeodeSolidMesh3D,
)

# Objects with a Z axis: alignment without distortion scales it too
CRS_GEODE_OBJECTS_3D = (
    GeodeBRep,
    GeodePointSet3D,
    GeodeEdgedCurve3D,
    GeodeSurfaceMesh3D,
    GeodeSolidMesh3D,
)

CrsGeodeObject = (
    GeodeBRep
    | GeodeSection
    | GeodePointSet2D
    | GeodePointSet3D
    | GeodeEdgedCurve2D
    | GeodeEdgedCurve3D
    | GeodeSurfaceMesh2D
    | GeodeSurfaceMesh3D
    | GeodeSolidMesh3D
)


@functools.cache
def geographic_coordinate_systems(
    is_3d: bool,  # noqa: FBT001 positional so the cache key stays simple
) -> dict[str, og_geosciences.GeographicCoordinateSystemInfo]:
    """Known geographic CRS by "AUTHORITY:CODE", built once: the list has thousands of entries."""
    infos = (
        og_geosciences.GeographicCoordinateSystem3D.geographic_coordinate_systems()
        if is_3d
        else og_geosciences.GeographicCoordinateSystem2D.geographic_coordinate_systems()
    )
    return {info.authority_code(): info for info in infos}


def known_geographic_info(
    geode_object: CrsGeodeObject, authority: str, code: str
) -> og_geosciences.GeographicCoordinateSystemInfo | None:
    """The listed CRS for authority:code, None when PROJ does not know it."""
    return geographic_coordinate_systems(geode_object.is_3d()).get(f"{authority}:{code}")


def geographic_info(
    crs_manager: og.CoordinateReferenceSystemManager2D | og.CoordinateReferenceSystemManager3D,
) -> og_geosciences.GeographicCoordinateSystemInfo | None:
    crs = crs_manager.active_coordinate_reference_system()
    if isinstance(
        crs,
        og_geosciences.GeographicCoordinateSystem2D | og_geosciences.GeographicCoordinateSystem3D,
    ):
        return crs.info()
    return None


def active_crs(geode_object: GeodeObject) -> dict[str, str] | None:
    """{authority, code, name} of the active geographic CRS, None otherwise."""
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        return None
    try:
        info = geographic_info(geode_object.crs_manager())
    except (ValueError, RuntimeError) as error:
        # The CRS is extra information: a model without component mesh, or a CRS the
        # geosciences library cannot read, must not fail the whole data response
        logger.warning("Cannot read the active CRS: %s", error)
        return None
    if info is None:
        return None
    return {"authority": info.authority, "code": info.code, "name": info.name}


def convert_xy_corners(
    bounds: tuple[float, float, float, float],
    source: og_geosciences.GeographicCoordinateSystemInfo,
    target: og_geosciences.GeographicCoordinateSystemInfo,
) -> list[tuple[float, float]]:
    """The four corners of bounds, given in source, converted to target.

    Raises RuntimeError when PROJ rejects coordinates outside either CRS domain.
    """
    x_min, y_min, x_max, y_max = bounds
    corners = GeodePointSet3D()
    builder = corners.builder()
    for x, y in ((x_min, y_min), (x_max, y_min), (x_min, y_max), (x_max, y_max)):
        builder.create_point(og.Point3D([x, y, 0.0]))
    corners.assign_crs(source.authority_code(), source)
    # Assigning then converting to the same CRS name is rejected by OpenGeode
    if source.authority_code() != target.authority_code():
        corners.convert_crs(target.authority_code(), target)
    points = (corners.point_set.point(index) for index in range(4))
    return [(point.value(0), point.value(1)) for point in points]


# Extents (south, north, west, east) PROJ declares for a CRS
AREA_OF_USE_QUERY = """
SELECT extent.south_lat, extent.north_lat, extent.west_lon, extent.east_lon
FROM usage JOIN extent
ON extent.auth_name = usage.extent_auth_name AND extent.code = usage.extent_code
WHERE usage.object_auth_name = ? AND usage.object_code = ?
AND usage.object_table_name IN ('projected_crs', 'geodetic_crs', 'compound_crs')
"""


# Projected CRS, alone or as the horizontal part of a compound CRS
PROJECTED_QUERY = """
SELECT 1 FROM projected_crs WHERE auth_name = ? AND code = ?
UNION
SELECT 1 FROM compound_crs JOIN projected_crs
ON projected_crs.auth_name = compound_crs.horiz_crs_auth_name
AND projected_crs.code = compound_crs.horiz_crs_code
WHERE compound_crs.auth_name = ? AND compound_crs.code = ?
"""


def _query_proj_database(query: str, parameters: tuple[str, ...]) -> list[tuple[Any, ...]] | None:
    """Rows from the PROJ database opengeode ships, None when it cannot be read.

    The bindings do not expose this information.
    """
    database = (Path(os.environ["PROJ_DATA"]) / "proj.db").resolve()
    try:
        with contextlib.closing(
            sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
        ) as connection:
            rows: list[tuple[Any, ...]] = connection.execute(query, parameters).fetchall()
    except sqlite3.Error as error:
        logger.warning("Cannot read the PROJ database: %s", error)
        return None
    return rows


@functools.cache
def area_of_use(authority: str, code: str) -> list[tuple[float, float, float, float]]:
    """Extents where PROJ declares the CRS usable, empty when unknown."""
    rows = _query_proj_database(AREA_OF_USE_QUERY, (authority, code)) or []
    return [(float(s), float(n), float(w), float(e)) for s, n, w, e in rows]


@functools.cache
def is_projected(authority: str, code: str) -> bool:
    """Whether the CRS measures X and Y as lengths, not angles. True when unknown."""
    rows = _query_proj_database(PROJECTED_QUERY, (authority, code, authority, code))
    return rows is None or len(rows) > 0


def _overlaps(
    latitudes: tuple[float, float],
    longitudes: tuple[float, float],
    area: tuple[float, float, float, float],
) -> bool:
    south, north, west, east = area
    if latitudes[1] < south or latitudes[0] > north:
        return False
    if west <= east:
        return longitudes[1] >= west and longitudes[0] <= east
    # The area crosses the antimeridian
    return longitudes[1] >= west or longitudes[0] <= east


def coordinates_implausible(
    geode_object: CrsGeodeObject, info: og_geosciences.GeographicCoordinateSystemInfo
) -> bool:
    """Whether the data XY extent, read in info, misses the area where info is used."""
    boxes = [mesh.bounding_box() for mesh in geode_object.crs_meshes()]
    # Without mesh, the infinite bounds below mark the data as implausible
    bounds = (
        min((box.min().value(0) for box in boxes), default=math.inf),
        min((box.min().value(1) for box in boxes), default=math.inf),
        max((box.max().value(0) for box in boxes), default=math.inf),
        max((box.max().value(1) for box in boxes), default=math.inf),
    )
    if not all(math.isfinite(value) for value in bounds):
        return True
    try:
        corners = convert_xy_corners(bounds, info, WGS84)
    except RuntimeError:
        return True
    latitudes = [latitude for latitude, _ in corners]
    longitudes = [longitude for _, longitude in corners]
    # Written as "not within" so NaN counts as outside
    if not all(abs(value) <= MAX_LATITUDE for value in latitudes) or not all(
        abs(value) <= MAX_LONGITUDE for value in longitudes
    ):
        return True
    areas = area_of_use(info.authority, info.code)
    if not areas:
        return False
    latitude_range = (min(latitudes), max(latitudes))
    longitude_range = (min(longitudes), max(longitudes))
    # Partial overlap is enough: models often go a little beyond the declared area
    return not any(_overlaps(latitude_range, longitude_range, area) for area in areas)


# Frames are fitted on a sample of the vertices: large meshes would be slow to scan in Python
MAX_FRAME_VERTICES = 10_000
MIN_FRAME_POINTS = 3


def _xy(
    crs: og.CoordinateReferenceSystem2D | og.CoordinateReferenceSystem3D, vertex: int
) -> list[float]:
    point = crs.point(vertex)
    return [point.value(0), point.value(1)]


def _cross(origin: list[float], first: list[float], second: list[float]) -> float:
    return (first[0] - origin[0]) * (second[1] - origin[1]) - (first[1] - origin[1]) * (
        second[0] - origin[0]
    )


def _frames(mesh: Mesh) -> tuple[og.CoordinateSystem2D, og.CoordinateSystem2D] | None:
    """The same three vertices as frames in the active and in the original CRS."""
    nb_vertices = mesh.nb_vertices()
    if nb_vertices < MIN_FRAME_POINTS:
        return None
    crs_manager = mesh.main_coordinate_reference_system_manager()
    active = crs_manager.active_coordinate_reference_system()
    original = crs_manager.find_coordinate_reference_system(ORIGINAL_CRS)
    vertices = range(0, nb_vertices, max(1, nb_vertices // MAX_FRAME_VERTICES))
    points = {vertex: _xy(active, vertex) for vertex in vertices}
    origin = points[0]
    # The farthest vertex, then the one spanning the largest triangle: the best conditioned frame
    first = max(
        vertices,
        key=lambda vertex: math.dist(origin, points[vertex]),
    )
    second = max(
        vertices,
        key=lambda vertex: abs(_cross(origin, points[first], points[vertex])),
    )
    span = math.dist(origin, points[first]) ** 2
    if span == 0 or abs(_cross(origin, points[first], points[second])) <= span * 1e-9:
        return None

    def frame(
        crs: og.CoordinateReferenceSystem2D | og.CoordinateReferenceSystem3D,
    ) -> og.CoordinateSystem2D:
        return og.CoordinateSystem2D(
            og.Point2D(_xy(crs, 0)), [og.Point2D(_xy(crs, first)), og.Point2D(_xy(crs, second))]
        )

    return frame(active), frame(original)


def original_coordinates(
    geode_object: CrsGeodeObject, points: list[og.Point2D]
) -> list[og.Point2D] | None:
    """Points given in the active CRS, expressed in the original coordinates.

    An alignment is affine: three vertices known in both CRS invert it (approximately when the
    data was converted since). None when no mesh has three non-colinear vertices.
    """
    for mesh in geode_object.crs_meshes():
        frames = _frames(mesh)
        if frames is not None:
            active, original = frames
            return [original.global_coordinates(active.coordinates(point)) for point in points]
    return None
