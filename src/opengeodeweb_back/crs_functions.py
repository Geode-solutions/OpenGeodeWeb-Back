from __future__ import annotations

# Standard library imports
from typing import TYPE_CHECKING

# Third party imports
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
    import opengeode as og

    from opengeodeweb_back.geode_objects.geode_object import GeodeObject

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
    except ValueError:  # A model without any component mesh has no CRS
        return None
    if info is None:
        return None
    return {"authority": info.authority, "code": info.code, "name": info.name}
