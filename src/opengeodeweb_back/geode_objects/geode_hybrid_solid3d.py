# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_solid_mesh3d import GeodeSolidMesh3D


class GeodeHybridSolid3D(GeodeSolidMesh3D):
    hybrid_solid: og.HybridSolid3D

    def __init__(self, hybrid_solid: og.HybridSolid3D | None = None) -> None:
        self.hybrid_solid = (
            hybrid_solid if hybrid_solid is not None else og.HybridSolid3D.create()
        )
        super().__init__(self.hybrid_solid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "HybridSolid3D"

    def native_extension(self) -> str:
        return self.hybrid_solid.native_extension()

    def builder(self) -> og.HybridSolidBuilder3D:
        return og.HybridSolidBuilder3D.create(self.hybrid_solid)

    @classmethod
    def load(cls, filename: str) -> GeodeHybridSolid3D:
        return GeodeHybridSolid3D(og.load_hybrid_solid3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.hybrid_solid_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_hybrid_solid_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.HybridSolidInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.HybridSolidOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.hybrid_solid_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_hybrid_solid_saveable3D(self.hybrid_solid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_hybrid_solid3D(self.hybrid_solid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_hybrid_solid3D(
            self.hybrid_solid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_hybrid_solid3D(
            self.hybrid_solid, filename_without_extension
        )
