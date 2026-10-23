from __future__ import annotations

# Standard library imports
import functools
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

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
    from opengeodeweb_back.geode_objects.geode_object import GeodeObject

logger = logging.getLogger(__name__)

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
