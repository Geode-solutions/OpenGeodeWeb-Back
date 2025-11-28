# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import geode_viewables as viewables

# Local application imports
from .types import GeodeModelType
from .geode_section import GeodeSection


class GeodeCrossSection(GeodeSection):
    cross_section: og_geosciences.CrossSection

    def __init__(
        self, cross_section: og_geosciences.CrossSection | None = None
    ) -> None:
        self.cross_section = (
            cross_section
            if cross_section is not None
            else og_geosciences.CrossSection()
        )
        super().__init__(self.cross_section)

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "CrossSection"

    def native_extension(self) -> str:
        return self.cross_section.native_extension()

    def builder(self) -> og_geosciences.CrossSectionBuilder:
        return og_geosciences.CrossSectionBuilder(self.cross_section)

    @classmethod
    def load(cls, filename: str) -> GeodeCrossSection:
        return GeodeCrossSection(og_geosciences.load_cross_section(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.cross_section_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_cross_section_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.CrossSectionInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.CrossSectionOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.cross_section_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_cross_section_saveable(self.cross_section, filename)

    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_cross_section(self.cross_section, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_cross_section(
            self.cross_section, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_cross_section(
            self.cross_section, filename_without_extension
        )
