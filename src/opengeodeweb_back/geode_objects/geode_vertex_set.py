# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

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


class GeodeVertexSet(GeodeMesh):
    vertex_set: og.VertexSet

    def __init__(self, vertex_set: og.VertexSet | None = None) -> None:
        self.vertex_set = (
            vertex_set if vertex_set is not None else og.VertexSet.create()
        )
        super().__init__(self.vertex_set)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "VertexSet"

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "points"

    @override
    def native_extension(self) -> str:
        return self.vertex_set.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return False

    @override
    def builder(self) -> og.VertexSetBuilder:
        return og.VertexSetBuilder.create(self.vertex_set)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeVertexSet:
        return GeodeVertexSet(og.load_vertex_set(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.vertex_set_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_vertex_set_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.VertexSetInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.VertexSetOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.vertex_set_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_vertex_set_saveable(self.vertex_set, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_vertex_set(self.vertex_set, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return ""

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return ""

    @override
    def inspect(self) -> object:
        return None

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.ObjectValidity()

    @override
    def vertex_attribute_manager(self) -> og.AttributeManager:
        return self.vertex_set.vertex_attribute_manager()
