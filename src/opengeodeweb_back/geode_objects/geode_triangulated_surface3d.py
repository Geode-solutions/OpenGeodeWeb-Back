# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og

# Local application imports
from .geode_surface_mesh3d import GeodeSurfaceMesh3D

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import GeodeMeshType


class GeodeTriangulatedSurface3D(GeodeSurfaceMesh3D):
    triangulated_surface: og.TriangulatedSurface3D

    def __init__(self, triangulated_surface: og.TriangulatedSurface3D | None = None) -> None:
        self.triangulated_surface = (
            triangulated_surface
            if triangulated_surface is not None
            else og.TriangulatedSurface3D.create()
        )
        super().__init__(self.triangulated_surface)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "TriangulatedSurface3D"

    @override
    def native_extension(self) -> str:
        return self.triangulated_surface.native_extension()

    @override
    def builder(self) -> og.TriangulatedSurfaceBuilder3D:
        return og.TriangulatedSurfaceBuilder3D.create(self.triangulated_surface)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeTriangulatedSurface3D:
        return GeodeTriangulatedSurface3D(og.load_triangulated_surface3D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.triangulated_surface_additional_files3D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_triangulated_surface_loadable3D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceInputFactory3D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.TriangulatedSurfaceOutputFactory3D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.triangulated_surface_object_priority3D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_triangulated_surface_saveable3D(self.triangulated_surface, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_triangulated_surface3D(self.triangulated_surface, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_triangulated_surface3D(
            self.triangulated_surface, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_triangulated_surface3D(
            self.triangulated_surface, filename_without_extension
        )
