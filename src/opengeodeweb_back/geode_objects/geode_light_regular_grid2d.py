# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_grid2d import GeodeGrid2D


class GeodeLightRegularGrid2D(GeodeGrid2D):
    light_regular_grid: og.LightRegularGrid2D

    def __init__(self, light_regular_grid: og.LightRegularGrid2D) -> None:
        self.light_regular_grid = light_regular_grid
        super().__init__(self.light_regular_grid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "LightRegularGrid2D"

    def native_extension(self) -> str:
        return self.light_regular_grid.native_extension()

    @classmethod
    def load(cls, filename: str) -> GeodeLightRegularGrid2D:
        return GeodeLightRegularGrid2D(og.load_light_regular_grid2D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.light_regular_grid_additional_files2D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_light_regular_grid_loadable2D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.LightRegularGridInputFactory2D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.LightRegularGridOutputFactory2D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.light_regular_grid_object_priority2D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_light_regular_grid_saveable2D(self.light_regular_grid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_light_regular_grid2D(self.light_regular_grid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_light_regular_grid2D(
            self.light_regular_grid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_light_regular_grid2D(
            self.light_regular_grid, filename_without_extension
        )

    def vertex_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.grid_vertex_attribute_manager()

    def cell_attribute_manager(self) -> og.AttributeManager:
        return self.light_regular_grid.cell_attribute_manager()
