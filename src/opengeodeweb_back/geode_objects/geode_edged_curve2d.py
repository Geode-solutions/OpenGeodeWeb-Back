# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_graph import GeodeGraph


class GeodeEdgedCurve2D(GeodeGraph):
    edged_curve: og.EdgedCurve2D

    def __init__(self, edged_curve: og.EdgedCurve2D | None = None) -> None:
        self.edged_curve = edged_curve if edged_curve is not None else og.EdgedCurve2D()
        super().__init__(self.edged_curve)

    @classmethod
    def geode_mesh_type(cls) -> GeodeMeshType:
        return "EdgedCurve2D"

    def native_extension(self) -> str:
        return self.edged_curve.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return False

    @classmethod
    def is_viewable(cls) -> bool:
        return False

    def builder(self) -> og.EdgedCurveBuilder2D:
        return og.EdgedCurveBuilder2D(self.edged_curve)

    @classmethod
    def load_mesh(cls, filename: str) -> GeodeEdgedCurve2D:
        return GeodeEdgedCurve2D(og.load_edged_curve2D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.edged_curve_additional_files2D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_edged_curve_loadable2D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.EdgedCurveInputFactory2D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.EdgedCurveOutputFactory2D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.edged_curve_object_priority2D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_edged_curve_saveable2D(self.edged_curve, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_edged_curve2D(self.edged_curve, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_edged_curve2D(
            self.edged_curve, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_edged_curve2D(
            self.edged_curve, filename_without_extension
        )

    def inspect(self) -> og_inspector.EdgedCurveInspectionResult:
        return og_inspector.inspect_edged_curve2D(self.edged_curve)
