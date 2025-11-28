# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_graph import GeodeGraph


class GeodeEdgedCurve3D(GeodeGraph):
    edged_curve: og.EdgedCurve3D

    def __init__(self, edged_curve: og.EdgedCurve3D | None = None) -> None:
        self.edged_curve = (
            edged_curve if edged_curve is not None else og.EdgedCurve3D.create()
        )
        super().__init__(self.edged_curve)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "EdgedCurve3D"

    def native_extension(self) -> str:
        return self.edged_curve.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.EdgedCurveBuilder3D:
        return og.EdgedCurveBuilder3D.create(self.edged_curve)

    @classmethod
    def load(cls, filename: str) -> GeodeEdgedCurve3D:
        return GeodeEdgedCurve3D(og.load_edged_curve3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.edged_curve_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_edged_curve_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.EdgedCurveInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.EdgedCurveOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.edged_curve_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_edged_curve_saveable3D(self.edged_curve, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_edged_curve3D(self.edged_curve, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_edged_curve3D(
            self.edged_curve, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_edged_curve3D(
            self.edged_curve, filename_without_extension
        )

    def inspect(self) -> og_inspector.EdgedCurveInspectionResult:
        return og_inspector.inspect_edged_curve3D(self.edged_curve)

    def assign_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.assign_edged_curve_geographic_coordinate_system_info3D(
            self.edged_curve, builder, crs_name, info
        )

    def convert_crs(
        self, crs_name: str, info: og_geosciences.GeographicCoordinateSystemInfo
    ) -> None:
        builder = self.builder()
        og_geosciences.convert_edged_curve_coordinate_reference_system3D(
            self.edged_curve, builder, crs_name, info
        )

    def create_crs(
        self, crs_name: str, input: og.CoordinateSystem2D, output: og.CoordinateSystem2D
    ) -> None:
        builder = self.builder()
        og.create_edged_curve_coordinate_system3D(
            self.edged_curve, builder, crs_name, input, output
        )
