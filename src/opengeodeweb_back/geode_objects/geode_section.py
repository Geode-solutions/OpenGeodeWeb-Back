# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeModelType, ViewerType
from .geode_model import GeodeModel, ComponentRegistry


class GeodeSection(GeodeModel):
    section: og.Section

    def __init__(self, section: og.Section | None = None) -> None:
        self.section = section if section is not None else og.Section()
        super().__init__(self.section)

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "Section"

    def native_extension(self) -> str:
        return self.section.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return False

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.SectionBuilder:
        return og.SectionBuilder(self.section)

    @classmethod
    def load(cls, filename: str) -> GeodeSection:
        return GeodeSection(og.load_section(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.section_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_section_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.SectionInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.SectionOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.section_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_section_saveable(self.section, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_section(self.section, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_section(self.section, filename_without_extension)

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_section(
            self.section, filename_without_extension
        )

    def mesh_components(self) -> ComponentRegistry:
        return self.section.mesh_components()

    def inspect(self) -> og_inspector.SectionInspectionResult:
        return og_inspector.inspect_section(self.section)

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
        self, crs_name: str, input: og.CoordinateSystem2D, output: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_section_coordinate_system(
            self.section, builder, crs_name, input, output
        )
