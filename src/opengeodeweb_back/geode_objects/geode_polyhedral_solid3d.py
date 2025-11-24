# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_solid_mesh3d import GeodeSolidMesh3D


class GeodePolyhedralSolid3D(GeodeSolidMesh3D):
    polyhedral_solid: og.PolyhedralSolid3D

    def __init__(self, polyhedral_solid: og.PolyhedralSolid3D | None = None) -> None:
        self.polyhedral_solid = (
            polyhedral_solid
            if polyhedral_solid is not None
            else og.PolyhedralSolid3D.create()
        )
        super().__init__(self.polyhedral_solid)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "PolyhedralSolid3D"

    def native_extension(self) -> str:
        return self.polyhedral_solid.native_extension()

    def builder(self) -> og.PolyhedralSolidBuilder3D:
        return og.PolyhedralSolidBuilder3D.create(self.polyhedral_solid)

    @classmethod
    def load(cls, filename: str) -> GeodePolyhedralSolid3D:
        return GeodePolyhedralSolid3D(og.load_polyhedral_solid3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.polyhedral_solid_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_polyhedral_solid_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.PolyhedralSolidInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.PolyhedralSolidOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.polyhedral_solid_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_polyhedral_solid_saveable3D(self.polyhedral_solid, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_polyhedral_solid3D(self.polyhedral_solid, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_polyhedral_solid3D(
            self.polyhedral_solid, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_polyhedral_solid3D(
            self.polyhedral_solid, filename_without_extension
        )
