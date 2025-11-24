# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType, ViewerType
from .geode_mesh import GeodeMesh


class GeodeVertexSet(GeodeMesh):
    vertex_set: og.VertexSet

    def __init__(self, vertex_set: og.VertexSet | None = None) -> None:
        self.vertex_set = (
            vertex_set if vertex_set is not None else og.VertexSet.create()
        )
        super().__init__(self.vertex_set)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "VertexSet"

    def native_extension(self) -> str:
        return self.vertex_set.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return False

    @classmethod
    def is_viewable(cls) -> bool:
        return False

    def builder(self) -> og.VertexSetBuilder:
        return og.VertexSetBuilder.create(self.vertex_set)

    @classmethod
    def load(cls, filename: str) -> GeodeVertexSet:
        return GeodeVertexSet(og.load_vertex_set(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.vertex_set_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_vertex_set_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.VertexSetInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.VertexSetOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.vertex_set_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_vertex_set_saveable(self.vertex_set, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_vertex_set(self.vertex_set, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return ""

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return ""

    def inspect(self) -> object:
        return None

    def vertex_attribute_manager(self) -> og.AttributeManager:
        return self.vertex_set.vertex_attribute_manager()
