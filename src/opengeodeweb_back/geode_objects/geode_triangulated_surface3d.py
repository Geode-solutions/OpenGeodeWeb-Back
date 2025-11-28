# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_surface_mesh3d import GeodeSurfaceMesh3D


class GeodeTriangulatedSurface3D(GeodeSurfaceMesh3D):
    triangulated_surface: og.TriangulatedSurface3D

    def __init__(
        self, triangulated_surface: og.TriangulatedSurface3D | None = None
    ) -> None:
        self.triangulated_surface = (
            triangulated_surface
            if triangulated_surface is not None
            else og.TriangulatedSurface3D.create()
        )
        super().__init__(self.triangulated_surface)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "TriangulatedSurface3D"

    def native_extension(self) -> str:
        return self.triangulated_surface.native_extension()

    def builder(self) -> og.TriangulatedSurfaceBuilder3D:
        return og.TriangulatedSurfaceBuilder3D.create(self.triangulated_surface)

    @classmethod
    def load(cls, filename: str) -> GeodeTriangulatedSurface3D:
        return GeodeTriangulatedSurface3D(og.load_triangulated_surface3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.triangulated_surface_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_triangulated_surface_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.triangulated_surface_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_triangulated_surface_saveable3D(
            self.triangulated_surface, filename
        )

    def save(self, filename: str) -> list[str]:
        return og.save_triangulated_surface3D(self.triangulated_surface, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_triangulated_surface3D(
            self.triangulated_surface, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_triangulated_surface3D(
            self.triangulated_surface, filename_without_extension
        )
