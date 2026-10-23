# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences

Mesh = (
    og.PointSet2D
    | og.PointSet3D
    | og.EdgedCurve2D
    | og.EdgedCurve3D
    | og.SurfaceMesh2D
    | og.SurfaceMesh3D
    | og.SolidMesh3D
)
CrsBuilder = (
    og.CoordinateReferenceSystemManagerBuilder2D | og.CoordinateReferenceSystemManagerBuilder3D
)


def _coordinates_name(
    crs: og.CoordinateReferenceSystem2D | og.CoordinateReferenceSystem3D,
) -> str | None:
    # A geographic CRS stores its coordinates in a vertex attribute named after the CRS
    if isinstance(
        crs,
        og_geosciences.GeographicCoordinateSystem2D | og_geosciences.GeographicCoordinateSystem3D,
    ):
        return crs.info().name
    return None


def delete_crs_with_coordinates(mesh: Mesh, crs_builder: CrsBuilder, crs_name: str) -> None:
    """Delete an inactive CRS and its coordinates: each conversion stores new ones."""
    crs_manager = mesh.main_coordinate_reference_system_manager()
    coordinates_name = _coordinates_name(crs_manager.find_coordinate_reference_system(crs_name))
    active_name = _coordinates_name(crs_manager.active_coordinate_reference_system())
    crs_builder.delete_coordinate_reference_system(crs_name)
    # Attributes are only found by name: keep them when the active CRS shares it
    if coordinates_name is None or coordinates_name == active_name:
        return
    attribute_manager = mesh.vertex_attribute_manager()
    for attribute_id in attribute_manager.attribute_ids_matching_name(coordinates_name) or []:
        attribute_manager.delete_attribute(attribute_id)
