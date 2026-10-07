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


class GeodeSection(GeodeModel):
    section: og.Section

    def __init__(self, section: og.Section | None = None) -> None:
        self.section = section if section is not None else og.Section()
        super().__init__(self.section)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "Section"

    @override
    def native_extension(self) -> str:
        return self.section.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    def builder(self) -> og.SectionBuilder:
        return og.SectionBuilder(self.section)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeSection:
        return GeodeSection(og.load_section(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.section_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_section_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.SectionInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.SectionOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.section_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_section_saveable(self.section, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_section(self.section, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_section(self.section, filename_without_extension)

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_section(self.section, filename_without_extension)

    @override
    def mesh_components(self) -> ComponentRegistry:
        return self.section.mesh_components()

    @override
    def collection_components(self) -> ComponentRegistry:
        return self.section.collection_components()

    @override
    def boundaries(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.section.boundaries(component_id)

    @override
    def internals(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.section.internals(component_id)

    @override
    def items(self, component_id: og.uuid) -> list[og.ComponentID]:
        return self.section.items(component_id)

    @override
    def component(self, component_id: og.uuid) -> og.Component2D:
        return self.section.section_component(component_id)

    @override
    def inspect(self) -> og_inspector.SectionInspectionResult:
        return og_inspector.inspect_section(self.section)

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.is_section_valid(self.section)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_section_geographic_coordinate_system_info(
            self.section, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_section_coordinate_reference_system(
            self.section, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input_crs: og.CoordinateSystem2D, output_crs: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_section_coordinate_system(self.section, builder, crs_name, input_crs, output_crs)
