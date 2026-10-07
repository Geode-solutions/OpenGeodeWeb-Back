# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode_geosciences as og_geosciences

# Local application imports
from .geode_section import GeodeSection

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import GeodeModelType


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

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "CrossSection"

    @override
    def native_extension(self) -> str:
        return self.cross_section.native_extension()

    @override
    def builder(self) -> og_geosciences.CrossSectionBuilder:
        return og_geosciences.CrossSectionBuilder(self.cross_section)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeCrossSection:
        return GeodeCrossSection(og_geosciences.load_cross_section(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.cross_section_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_cross_section_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.CrossSectionInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.CrossSectionOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.cross_section_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_cross_section_saveable(self.cross_section, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_cross_section(self.cross_section, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_cross_section(
            self.cross_section, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_cross_section(
            self.cross_section, filename_without_extension
        )

    def component_name(self, component_id: og.uuid) -> str | None:
        return self.cross_section.cross_section_component(component_id).name()

    @override
    def component(self, component_id: og.uuid) -> og.Component2D:
        return self.cross_section.cross_section_component(component_id)
