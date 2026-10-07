# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector

# Local application imports
from .geode_mesh import GeodeMesh

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import (
        GeodeMeshType,
        ViewerElementsType,
    )


class GeodeRasterImage2D(GeodeMesh):
    raster_image: og.RasterImage2D

    def __init__(self, raster_image: og.RasterImage2D) -> None:
        self.raster_image = raster_image
        super().__init__(self.raster_image)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "RasterImage2D"

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "polygons"

    @override
    def native_extension(self) -> str:
        return self.raster_image.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    def builder(self) -> og.IdentifierBuilder:
        return og.IdentifierBuilder(self.raster_image)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeRasterImage2D:
        return GeodeRasterImage2D(og.load_raster_image2D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.raster_image_additional_files2D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_raster_image_loadable2D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.RasterImageInputFactory2D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.RasterImageOutputFactory2D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.raster_image_object_priority2D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_raster_image_saveable2D(self.raster_image, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_raster_image2D(self.raster_image, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_raster_image2D(
            self.raster_image, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_raster_image2D(
            self.raster_image, filename_without_extension
        )

    @override
    def inspect(self) -> None:
        return None

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.ObjectValidity()

    @override
    def vertex_attribute_manager(self) -> og.AttributeManager:
        return og.AttributeManager()
