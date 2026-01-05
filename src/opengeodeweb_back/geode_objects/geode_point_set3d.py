# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_vertex_set import GeodeVertexSet


class GeodePointSet3D(GeodeVertexSet):
    point_set: og.PointSet3D

    def __init__(self, point_set: og.PointSet3D | None = None) -> None:
        self.point_set = point_set if point_set is not None else og.PointSet3D.create()
        super().__init__(self.point_set)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "PointSet3D"

    def native_extension(self) -> str:
        return self.point_set.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.PointSetBuilder3D:
        return og.PointSetBuilder3D.create(self.point_set)

    @classmethod
    def load(cls, filename: str) -> GeodePointSet3D:
        return GeodePointSet3D(og.load_point_set3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.point_set_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_point_set_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.PointSetInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.PointSetOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.point_set_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_point_set_saveable3D(self.point_set, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_point_set3D(self.point_set, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_point_set3D(
            self.point_set, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_point_set3D(
            self.point_set, filename_without_extension
        )

    def inspect(self) -> og_inspector.PointSetInspectionResult:
        return og_inspector.inspect_point_set3D(self.point_set)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_point_set_geographic_coordinate_system_info3D(
            self.point_set, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_point_set_coordinate_reference_system3D(
            self.point_set, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input: og.CoordinateSystem2D, output: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_point_set_coordinate_system3D(
            self.point_set, builder, crs_name, input, output
        )
