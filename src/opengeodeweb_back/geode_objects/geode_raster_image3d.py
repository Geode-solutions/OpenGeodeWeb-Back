# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_mesh import GeodeMesh


class GeodeRasterImage3D(GeodeMesh):
    raster_image: og.RasterImage3D

    def __init__(self, raster_image: og.RasterImage3D) -> None:
        self.raster_image = raster_image
        super().__init__(self.raster_image)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "RasterImage3D"

    def native_extension(self) -> str:
        return self.raster_image.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> None:
        return None

    @classmethod
    def load(cls, filename: str) -> GeodeRasterImage3D:
        return GeodeRasterImage3D(og.load_raster_image3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.raster_image_additional_files3D(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_raster_image_loadable3D(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.RasterImageInputFactory3D.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.RasterImageOutputFactory3D.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.raster_image_object_priority3D(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_raster_image_saveable3D(self.raster_image, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_raster_image3D(self.raster_image, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_raster_image3D(
            self.raster_image, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_raster_image3D(
            self.raster_image, filename_without_extension
        )

    def inspect(self) -> None:
        return None

    def vertex_attribute_manager(self) -> og.AttributeManager:
        return og.AttributeManager()
