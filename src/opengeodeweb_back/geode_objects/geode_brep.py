# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector

# Local application imports
from .crs_coordinates import delete_crs_with_coordinates, scale_z
from .geode_model import ComponentRegistry, GeodeModel

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import GeodeModelType

    from .crs_coordinates import Mesh


class GeodeBRep(GeodeModel):
    brep: og.BRep

    def __init__(self, brep: og.BRep | None = None) -> None:
        self.brep = brep if brep is not None else og.BRep()
        super().__init__(self.brep)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "BRep"

    @override
    def native_extension(self) -> str:
        return self.brep.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return True

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    def builder(self) -> og.BRepBuilder:
        return og.BRepBuilder(self.brep)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeBRep:
        return GeodeBRep(og.load_brep(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.brep_additional_files(filename)

    @classmethod
    def time_series_input_extensions(cls) -> list[str]:
        return og.BRepTimeSeriesInputFactory.list_creators()

    @classmethod
    def time_series_additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.brep_time_series_additional_files(filename)

    def load_time_series(self, filename: str) -> None:
        og.load_brep_time_series(self.brep, filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_brep_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.BRepInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.BRepOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.brep_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_brep_saveable(self.brep, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_brep(self.brep, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_brep(self.brep, filename_without_extension)

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_brep(self.brep, filename_without_extension)

    @override
    def mesh_components(self) -> ComponentRegistry:
        return self.brep.mesh_components()

    @override
    def collection_components(self) -> ComponentRegistry:
        return self.brep.collection_components()

    @override
    def boundaries(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.brep.boundaries(component_id)

    @override
    def internals(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.brep.internals(component_id)

    @override
    def items(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.brep.items(component_id)

    @override
    def component(self, component_id: og.uuid) -> og.Component3D:
        return self.brep.brep_component(component_id)

    @override
    def inspect(self) -> og_inspector.BRepInspectionResult:
        return og_inspector.inspect_brep(self.brep)

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.is_brep_valid(self.brep)

    def crs_manager(self) -> og.CoordinateReferenceSystemManager3D:
        # Models have no CRS manager of their own: CRS are assigned to every component mesh
        for components in (
            self.brep.corners(),
            self.brep.lines(),
            self.brep.surfaces(),
            self.brep.blocks(),
        ):
            for component in components:
                return component.mesh().main_coordinate_reference_system_manager()
        msg = "BRep has no mesh component"
        raise ValueError(msg)

    def delete_crs(self, crs_name: str) -> None:
        # Models have no CRS manager of their own: the CRS lives on every component mesh
        builder = self.builder()
        for corner in self.brep.corners():
            crs_builder = builder.corner_mesh_builder(
                corner
            ).main_coordinate_reference_system_manager_builder()
            delete_crs_with_coordinates(corner.mesh(), crs_builder, crs_name)
        for line in self.brep.lines():
            crs_builder = builder.line_mesh_builder(
                line
            ).main_coordinate_reference_system_manager_builder()
            delete_crs_with_coordinates(line.mesh(), crs_builder, crs_name)
        for surface in self.brep.surfaces():
            crs_builder = builder.surface_mesh_builder(
                surface
            ).main_coordinate_reference_system_manager_builder()
            delete_crs_with_coordinates(surface.mesh(), crs_builder, crs_name)
        for block in self.brep.blocks():
            crs_builder = builder.block_mesh_builder(
                block
            ).main_coordinate_reference_system_manager_builder()
            delete_crs_with_coordinates(block.mesh(), crs_builder, crs_name)

    def set_active_crs(self, crs_name: str) -> None:
        # Models have no CRS manager of their own: activate the CRS on every component mesh
        builder = self.builder()
        for corner in self.brep.corners():
            crs_builder = builder.corner_mesh_builder(
                corner
            ).main_coordinate_reference_system_manager_builder()
            crs_builder.set_active_coordinate_reference_system(crs_name)
        for line in self.brep.lines():
            crs_builder = builder.line_mesh_builder(
                line
            ).main_coordinate_reference_system_manager_builder()
            crs_builder.set_active_coordinate_reference_system(crs_name)
        for surface in self.brep.surfaces():
            crs_builder = builder.surface_mesh_builder(
                surface
            ).main_coordinate_reference_system_manager_builder()
            crs_builder.set_active_coordinate_reference_system(crs_name)
        for block in self.brep.blocks():
            crs_builder = builder.block_mesh_builder(
                block
            ).main_coordinate_reference_system_manager_builder()
            crs_builder.set_active_coordinate_reference_system(crs_name)

    def crs_meshes(self) -> list[Mesh]:
        # Models have no CRS manager of their own: CRS live on every component mesh
        meshes: list[Mesh] = []
        meshes.extend(corner.mesh() for corner in self.brep.corners())
        meshes.extend(line.mesh() for line in self.brep.lines())
        meshes.extend(surface.mesh() for surface in self.brep.surfaces())
        meshes.extend(block.mesh() for block in self.brep.blocks())
        return meshes

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_brep_geographic_coordinate_system_info(
            self.brep, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_brep_coordinate_reference_system(self.brep, builder, crs_name, info)

    def create_crs(
        self,
        crs_name: str,
        input_crs: og.CoordinateSystem2D,
        output_crs: og.CoordinateSystem2D,
    ) -> None:
        builder = self.builder()
        og.create_brep_coordinate_system(self.brep, builder, crs_name, input_crs, output_crs)

    def scale_z(self, factor: float) -> None:
        # Models have no CRS manager of their own: every component mesh is scaled
        builder = self.builder()
        for corner in self.brep.corners():
            scale_z(corner.mesh(), builder.corner_mesh_builder(corner), factor)
        for line in self.brep.lines():
            scale_z(line.mesh(), builder.line_mesh_builder(line), factor)
        for surface in self.brep.surfaces():
            scale_z(surface.mesh(), builder.surface_mesh_builder(surface), factor)
        for block in self.brep.blocks():
            scale_z(block.mesh(), builder.block_mesh_builder(block), factor)
