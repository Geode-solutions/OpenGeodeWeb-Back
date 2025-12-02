# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_solid_mesh3d import GeodeSolidMesh3D


class GeodeTetrahedralSolid3D(GeodeSolidMesh3D):
    tetrahedral_solid: og.TetrahedralSolid3D

    def __init__(self, tetrahedral_solid: og.TetrahedralSolid3D | None = None) -> None:
        self.tetrahedral_solid = (
            tetrahedral_solid
            if tetrahedral_solid is not None
            else og.TetrahedralSolid3D.create()
        )
        super().__init__(self.tetrahedral_solid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "TetrahedralSolid3D"

    def native_extension(self) -> str:
        return self.tetrahedral_solid.native_extension()

    def builder(self) -> og.TetrahedralSolidBuilder3D:
        return og.TetrahedralSolidBuilder3D.create(self.tetrahedral_solid)

    @classmethod
    def load(cls, filename: str) -> GeodeTetrahedralSolid3D:
        return GeodeTetrahedralSolid3D(og.load_tetrahedral_solid3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.tetrahedral_solid_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_tetrahedral_solid_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.TetrahedralSolidInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.TetrahedralSolidOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.tetrahedral_solid_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_tetrahedral_solid_saveable3D(self.tetrahedral_solid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_tetrahedral_solid3D(self.tetrahedral_solid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_tetrahedral_solid3D(
            self.tetrahedral_solid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_tetrahedral_solid3D(
            self.tetrahedral_solid, filename_without_extension
        )
