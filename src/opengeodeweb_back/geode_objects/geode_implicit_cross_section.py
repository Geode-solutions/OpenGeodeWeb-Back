# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode_geosciences as og_geosciences

# Local application imports
from .geode_cross_section import GeodeCrossSection

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import GeodeModelType


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

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "ImplicitCrossSection"

    @override
    def native_extension(self) -> str:
        return self.implicit_cross_section.native_extension()

    @override
    def builder(self) -> og_geosciences.ImplicitCrossSectionBuilder:
        return og_geosciences.ImplicitCrossSectionBuilder(self.implicit_cross_section)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeImplicitCrossSection:
        return GeodeImplicitCrossSection(og_geosciences.load_implicit_cross_section(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.implicit_cross_section_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_implicit_cross_section_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitCrossSectionInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitCrossSectionOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.implicit_cross_section_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_implicit_cross_section_saveable(
            self.implicit_cross_section, filename
        )

    @override
    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_implicit_cross_section(self.implicit_cross_section, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_implicit_cross_section(
            self.implicit_cross_section, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_implicit_cross_section(
            self.implicit_cross_section, filename_without_extension
        )
