# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_surface_mesh2d import GeodeSurfaceMesh2D


class GeodeTriangulatedSurface2D(GeodeSurfaceMesh2D):
    triangulated_surface: og.TriangulatedSurface2D

    def __init__(
        self, triangulated_surface: og.TriangulatedSurface2D | None = None
    ) -> None:
        self.triangulated_surface = (
            triangulated_surface
            if triangulated_surface is not None
            else og.TriangulatedSurface2D.create()
        )
        super().__init__(self.triangulated_surface)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "TriangulatedSurface2D"

    def native_extension(self) -> str:
        return self.triangulated_surface.native_extension()

    def builder(self) -> og.TriangulatedSurfaceBuilder2D:
        return og.TriangulatedSurfaceBuilder2D.create(self.triangulated_surface)

    @classmethod
    def load(cls, filename: str) -> GeodeTriangulatedSurface2D:
        return GeodeTriangulatedSurface2D(og.load_triangulated_surface2D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.triangulated_surface_additional_files2D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_triangulated_surface_loadable2D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceInputFactory2D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceOutputFactory2D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.triangulated_surface_object_priority2D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_triangulated_surface_saveable2D(
            self.triangulated_surface, filename
        )

    def save(self, filename: str) -> list[str]:
        return og.save_triangulated_surface2D(self.triangulated_surface, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_triangulated_surface2D(
            self.triangulated_surface, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_triangulated_surface2D(
            self.triangulated_surface, filename_without_extension
        )
