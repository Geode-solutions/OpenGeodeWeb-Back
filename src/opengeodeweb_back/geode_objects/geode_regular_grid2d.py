# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og

from .geode_grid2d import GeodeGrid2D

# Local application imports
from .geode_surface_mesh2d import GeodeSurfaceMesh2D

if TYPE_CHECKING:
    import opengeode_inspector as og_inspector
    from opengeodeweb_microservice.database.data_types import GeodeMeshType


class GeodeRegularGrid2D(GeodeSurfaceMesh2D, GeodeGrid2D):
    regular_grid: og.RegularGrid2D

    def __init__(self, regular_grid: og.RegularGrid2D | None = None) -> None:
        self.regular_grid = regular_grid if regular_grid is not None else og.RegularGrid2D.create()
        super().__init__(self.regular_grid)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "RegularGrid2D"

    @override
    def inspect(self) -> og_inspector.SurfaceInspectionResult:
        return super().inspect()

    @override
    def native_extension(self) -> str:
        return self.regular_grid.native_extension()

    @override
    def builder(self) -> og.RegularGridBuilder2D:
        return og.RegularGridBuilder2D.create(self.regular_grid)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeRegularGrid2D:
        return GeodeRegularGrid2D(og.load_regular_grid2D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.regular_grid_additional_files2D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_regular_grid_loadable2D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.RegularGridInputFactory2D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.RegularGridOutputFactory2D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.regular_grid_object_priority2D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_regular_grid_saveable2D(self.regular_grid, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_regular_grid2D(self.regular_grid, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_regular_grid2D(self.regular_grid, filename_without_extension)

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_regular_grid2D(
            self.regular_grid, filename_without_extension
        )

    @override
    def cell_attribute_manager(self) -> og.AttributeManager:
        return self.regular_grid.cell_attribute_manager()
