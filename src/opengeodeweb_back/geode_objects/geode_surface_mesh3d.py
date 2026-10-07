# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector

# Local application imports
from .geode_vertex_set import GeodeVertexSet

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import ViewerElementsType


class GeodeSurfaceMesh3D(GeodeVertexSet):
    surface_mesh: og.SurfaceMesh3D

    def __init__(self, surface_mesh: og.SurfaceMesh3D | None = None) -> None:
        self.surface_mesh = (
            surface_mesh if surface_mesh is not None else og.SurfaceMesh3D.create()
        )
        super().__init__(self.surface_mesh)

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return True

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "polygons"

    @override
    def builder(self) -> og.SurfaceMeshBuilder3D:
        return og.SurfaceMeshBuilder3D.create(self.surface_mesh)

    @override
    def inspect(self) -> og_inspector.SurfaceInspectionResult:
        return og_inspector.inspect_surface3D(self.surface_mesh)

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.is_surface_valid3D(self.surface_mesh)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_surface_mesh_geographic_coordinate_system_info3D(
            self.surface_mesh, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_surface_mesh_coordinate_reference_system3D(
            self.surface_mesh, builder, crs_name, info
        )

    def create_crs(
        self,
        crs_name: str,
        input_crs: og.CoordinateSystem2D,
        output_crs: og.CoordinateSystem2D,
    ) -> None:
        builder = self.builder()
        og.create_surface_mesh_coordinate_system3D(
            self.surface_mesh, builder, crs_name, input_crs, output_crs
        )

    def polygon_attribute_manager(self) -> og.AttributeManager:
        return self.surface_mesh.polygon_attribute_manager()

    def texture_manager(self) -> og.TextureManager2D:
        return self.surface_mesh.texture_manager()
