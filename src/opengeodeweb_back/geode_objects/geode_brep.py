# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector

# Local application imports
from .geode_model import ComponentRegistry, GeodeModel

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import GeodeModelType


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
