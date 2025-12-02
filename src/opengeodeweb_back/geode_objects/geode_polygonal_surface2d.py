# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_surface_mesh2d import GeodeSurfaceMesh2D


class GeodePolygonalSurface2D(GeodeSurfaceMesh2D):
    polygonal_surface: og.PolygonalSurface2D

    def __init__(self, polygonal_surface: og.PolygonalSurface2D | None = None) -> None:
        self.polygonal_surface = (
            polygonal_surface
            if polygonal_surface is not None
            else og.PolygonalSurface2D.create()
        )
        super().__init__(self.polygonal_surface)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "PolygonalSurface2D"

    def native_extension(self) -> str:
        return self.polygonal_surface.native_extension()

    def builder(self) -> og.PolygonalSurfaceBuilder2D:
        return og.PolygonalSurfaceBuilder2D.create(self.polygonal_surface)

    @classmethod
    def load(cls, filename: str) -> GeodePolygonalSurface2D:
        return GeodePolygonalSurface2D(og.load_polygonal_surface2D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.polygonal_surface_additional_files2D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_polygonal_surface_loadable2D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.PolygonalSurfaceInputFactory2D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.PolygonalSurfaceOutputFactory2D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.polygonal_surface_object_priority2D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_polygonal_surface_saveable2D(self.polygonal_surface, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_polygonal_surface2D(self.polygonal_surface, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_polygonal_surface2D(
            self.polygonal_surface, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_polygonal_surface2D(
            self.polygonal_surface, filename_without_extension
        )
