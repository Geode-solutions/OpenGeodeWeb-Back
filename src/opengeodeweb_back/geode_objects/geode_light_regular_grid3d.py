# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og

# Local application imports
from .geode_grid3d import GeodeGrid3D

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import GeodeMeshType


class GeodeLightRegularGrid3D(GeodeGrid3D):
    light_regular_grid: og.LightRegularGrid3D

    def __init__(self, light_regular_grid: og.LightRegularGrid3D) -> None:
        self.light_regular_grid = light_regular_grid
        super().__init__(self.light_regular_grid)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "LightRegularGrid3D"

    @override
    def native_extension(self) -> str:
        return self.light_regular_grid.native_extension()

    @override
    def builder(self) -> og.IdentifierBuilder:
        return og.IdentifierBuilder(self.light_regular_grid)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeLightRegularGrid3D:
        return GeodeLightRegularGrid3D(og.load_light_regular_grid3D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.light_regular_grid_additional_files3D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_light_regular_grid_loadable3D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.LightRegularGridInputFactory3D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.LightRegularGridOutputFactory3D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.light_regular_grid_object_priority3D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_light_regular_grid_saveable3D(self.light_regular_grid, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_light_regular_grid3D(self.light_regular_grid, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_light_regular_grid3D(
            self.light_regular_grid, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_light_regular_grid3D(
            self.light_regular_grid, filename_without_extension
        )

    @override
    def vertex_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.grid_vertex_attribute_manager()

    @override
    def cell_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.cell_attribute_manager()
