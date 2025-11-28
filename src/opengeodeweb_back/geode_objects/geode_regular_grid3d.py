# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_solid_mesh3d import GeodeSolidMesh3D
from .geode_grid3d import GeodeGrid3D


class GeodeRegularGrid3D(GeodeSolidMesh3D, GeodeGrid3D):
    regular_grid: og.RegularGrid3D

    def __init__(self, regular_grid: og.RegularGrid3D | None = None) -> None:
        self.regular_grid = (
            regular_grid if regular_grid is not None else og.RegularGrid3D.create()
        )
        super().__init__(self.regular_grid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "RegularGrid3D"

    def native_extension(self) -> str:
        return self.regular_grid.native_extension()

    def builder(self) -> og.RegularGridBuilder3D:
        return og.RegularGridBuilder3D.create(self.regular_grid)

    @classmethod
    def load(cls, filename: str) -> GeodeRegularGrid3D:
        return GeodeRegularGrid3D(og.load_regular_grid3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.regular_grid_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_regular_grid_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.RegularGridInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.RegularGridOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.regular_grid_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_regular_grid_saveable3D(self.regular_grid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_regular_grid3D(self.regular_grid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_regular_grid3D(
            self.regular_grid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_regular_grid3D(
            self.regular_grid, filename_without_extension
        )

    def cell_attribute_manager(self) -> og.AttributeManager:
        return self.regular_grid.cell_attribute_manager()

    def inspect(self) -> og_inspector.SolidInspectionResult:
        return super().inspect()
