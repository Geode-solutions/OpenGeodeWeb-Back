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
Mesh3D = og.PointSet3D | og.EdgedCurve3D | og.SurfaceMesh3D | og.SolidMesh3D
MeshBuilder3D = (
    og.PointSetBuilder3D | og.EdgedCurveBuilder3D | og.SurfaceMeshBuilder3D | og.SolidMeshBuilder3D
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
    # Model components may not all hold the same CRS
    if not crs_manager.coordinate_reference_system_exists(crs_name):
        return
    coordinates_name = _coordinates_name(crs_manager.find_coordinate_reference_system(crs_name))
    active_name = _coordinates_name(crs_manager.active_coordinate_reference_system())
    crs_builder.delete_coordinate_reference_system(crs_name)
    # Attributes are only found by name: keep them when the active CRS shares it
    if coordinates_name is None or coordinates_name == active_name:
        return
    attribute_manager = mesh.vertex_attribute_manager()
    for attribute_id in attribute_manager.attribute_ids_matching_name(coordinates_name) or []:
        attribute_manager.delete_attribute(attribute_id)


def scale_z(mesh: Mesh3D, builder: MeshBuilder3D, factor: float) -> None:
    """Scale the active coordinates along Z around Z = 0."""
    for vertex in range(mesh.nb_vertices()):
        point = mesh.point(vertex)
        builder.set_point(
            vertex, og.Point3D([point.value(0), point.value(1), point.value(2) * factor])
        )
