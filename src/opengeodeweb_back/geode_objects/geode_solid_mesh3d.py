# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_vertex_set import GeodeVertexSet


class GeodeSolidMesh3D(GeodeVertexSet):
    solid_mesh: og.SolidMesh3D

    def __init__(self, solid_mesh: og.SolidMesh3D | None = None) -> None:
        self.solid_mesh = solid_mesh if solid_mesh is not None else og.SolidMesh3D()
        super().__init__(self.solid_mesh)

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.SolidMeshBuilder3D:
        return og.SolidMeshBuilder3D.create(self.solid_mesh)

    def inspect(self) -> og_inspector.SolidInspectionResult:
        return og_inspector.inspect_solid3D(self.solid_mesh)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_solid_mesh_geographic_coordinate_system_info3D(
            self.solid_mesh, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_solid_mesh_coordinate_reference_system3D(
            self.solid_mesh, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input: og.CoordinateSystem2D, output: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_solid_mesh_coordinate_system3D(
            self.solid_mesh, builder, crs_name, input, output
        )

    def polyhedron_attribute_manager(self) -> og.AttributeManager:
        return self.solid_mesh.polyhedron_attribute_manager()
