# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import geode_viewables as viewables

# Local application imports
from .types import GeodeModelType
from .geode_cross_section import GeodeCrossSection


class GeodeImplicitCrossSection(GeodeCrossSection):
    implicit_cross_section: og_geosciences.ImplicitCrossSection

    def __init__(
        self, implicit_cross_section: og_geosciences.ImplicitCrossSection | None = None
    ) -> None:
        self.implicit_cross_section = (
            implicit_cross_section
            if implicit_cross_section is not None
            else og_geosciences.ImplicitCrossSection()
        )
        super().__init__(self.implicit_cross_section)

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "ImplicitCrossSection"

    def native_extension(self) -> str:
        return self.implicit_cross_section.native_extension()

    def builder(self) -> og_geosciences.ImplicitCrossSectionBuilder:
        return og_geosciences.ImplicitCrossSectionBuilder(self.implicit_cross_section)

    @classmethod
    def load(cls, filename: str) -> GeodeImplicitCrossSection:
        return GeodeImplicitCrossSection(
            og_geosciences.load_implicit_cross_section(filename)
        )

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.implicit_cross_section_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_implicit_cross_section_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitCrossSectionInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitCrossSectionOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.implicit_cross_section_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_implicit_cross_section_saveable(
            self.implicit_cross_section, filename
        )

    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_implicit_cross_section(
            self.implicit_cross_section, filename
        )

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_implicit_cross_section(
            self.implicit_cross_section, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_implicit_cross_section(
            self.implicit_cross_section, filename_without_extension
        )
