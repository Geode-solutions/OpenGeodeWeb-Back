# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeModelType
from .geode_model import GeodeModel, ComponentRegistry


class GeodeBRep(GeodeModel):
    brep: og.BRep

    def __init__(self, brep: og.BRep | None = None) -> None:
        self.brep = brep if brep is not None else og.BRep()
        super().__init__(self.brep)

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "BRep"

    def native_extension(self) -> str:
        return self.brep.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.BRepBuilder:
        return og.BRepBuilder(self.brep)

    @classmethod
    def load(cls, filename: str) -> GeodeBRep:
        return GeodeBRep(og.load_brep(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.brep_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_brep_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.BRepInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.BRepOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.brep_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_brep_saveable(self.brep, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_brep(self.brep, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_brep(self.brep, filename_without_extension)

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_brep(self.brep, filename_without_extension)

    def mesh_components(self) -> ComponentRegistry:
        return self.brep.mesh_components()

    def inspect(self) -> og_inspector.BRepInspectionResult:
        return og_inspector.inspect_brep(self.brep)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_brep_geographic_coordinate_system_info(
            self.brep, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_brep_coordinate_reference_system(
            self.brep, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input: og.CoordinateSystem2D, output: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_brep_coordinate_system(self.brep, builder, crs_name, input, output)
