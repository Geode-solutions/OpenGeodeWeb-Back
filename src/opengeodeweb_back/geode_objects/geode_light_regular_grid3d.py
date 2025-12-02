# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_grid3d import GeodeGrid3D


class GeodeLightRegularGrid3D(GeodeGrid3D):
    light_regular_grid: og.LightRegularGrid3D

    def __init__(self, light_regular_grid: og.LightRegularGrid3D) -> None:
        self.light_regular_grid = light_regular_grid
        super().__init__(self.light_regular_grid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "LightRegularGrid3D"

    def native_extension(self) -> str:
        return self.light_regular_grid.native_extension()

    @classmethod
    def load(cls, filename: str) -> GeodeLightRegularGrid3D:
        return GeodeLightRegularGrid3D(og.load_light_regular_grid3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.light_regular_grid_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_light_regular_grid_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.LightRegularGridInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.LightRegularGridOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.light_regular_grid_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_light_regular_grid_saveable3D(self.light_regular_grid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_light_regular_grid3D(self.light_regular_grid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_light_regular_grid3D(
            self.light_regular_grid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_light_regular_grid3D(
            self.light_regular_grid, filename_without_extension
        )

    def vertex_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.grid_vertex_attribute_manager()

    def cell_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.cell_attribute_manager()
