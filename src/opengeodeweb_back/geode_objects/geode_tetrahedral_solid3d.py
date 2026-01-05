# Standard library imports
from __future__ import annotations
from typing import cast

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
        return cast(str, self.tetrahedral_solid.native_extension())

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
        return cast(list[str], og.TetrahedralSolidInputFactory3D.list_creators())

    @classmethod
    def output_extensions(cls) -> list[str]:
        return cast(list[str], og.TetrahedralSolidOutputFactory3D.list_creators())

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return cast(int, og.tetrahedral_solid_object_priority3D(filename))

    def is_saveable(self, filename: str) -> bool:
        return cast(
            bool, og.is_tetrahedral_solid_saveable3D(self.tetrahedral_solid, filename)
        )

    def save(self, filename: str) -> list[str]:
        return cast(
            list[str], og.save_tetrahedral_solid3D(self.tetrahedral_solid, filename)
        )

    def save_viewable(self, filename_without_extension: str) -> str:
        return cast(
            str,
            viewables.save_viewable_tetrahedral_solid3D(
                self.tetrahedral_solid, filename_without_extension
            ),
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return cast(
            str,
            viewables.save_light_viewable_tetrahedral_solid3D(
                self.tetrahedral_solid, filename_without_extension
            ),
        )
