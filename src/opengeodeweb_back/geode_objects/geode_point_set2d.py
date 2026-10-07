# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector

# Local application imports
from .geode_vertex_set import GeodeVertexSet

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import GeodeMeshType


class GeodePointSet2D(GeodeVertexSet):
    point_set: og.PointSet2D

    def __init__(self, point_set: og.PointSet2D | None = None) -> None:
        self.point_set = point_set if point_set is not None else og.PointSet2D.create()
        super().__init__(self.point_set)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "PointSet2D"

    @override
    def native_extension(self) -> str:
        return self.point_set.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    def builder(self) -> og.PointSetBuilder2D:
        return og.PointSetBuilder2D.create(self.point_set)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodePointSet2D:
        return GeodePointSet2D(og.load_point_set2D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.point_set_additional_files2D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_point_set_loadable2D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.PointSetInputFactory2D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.PointSetOutputFactory2D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.point_set_object_priority2D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_point_set_saveable2D(self.point_set, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_point_set2D(self.point_set, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_point_set2D(self.point_set, filename_without_extension)

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_point_set2D(self.point_set, filename_without_extension)

    @override
    def inspect(self) -> og_inspector.PointSetInspectionResult:
        return og_inspector.inspect_point_set2D(self.point_set)

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.is_pointset_valid2D(self.point_set)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_point_set_geographic_coordinate_system_info2D(
            self.point_set, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_point_set_coordinate_reference_system2D(
            self.point_set, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input_crs: og.CoordinateSystem2D, output_crs: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_point_set_coordinate_system2D(
            self.point_set, builder, crs_name, input_crs, output_crs
        )
