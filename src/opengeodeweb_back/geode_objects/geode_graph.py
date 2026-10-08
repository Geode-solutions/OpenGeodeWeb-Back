# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector

# Local application imports
from .geode_vertex_set import GeodeVertexSet

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import (
        GeodeMeshType,
        ViewerElementsType,
    )


class GeodeGraph(GeodeVertexSet):
    graph: og.Graph

    def __init__(self, graph: og.Graph | None = None) -> None:
        self.graph = graph if graph is not None else og.Graph.create()
        super().__init__(self.graph)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "Graph"

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "edges"

    @override
    def native_extension(self) -> str:
        return self.graph.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return False

    @override
    def builder(self) -> og.GraphBuilder:
        return og.GraphBuilder.create(self.graph)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeGraph:
        return GeodeGraph(og.load_graph(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.graph_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_graph_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.GraphInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.GraphOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.graph_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og.is_graph_saveable(self.graph, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og.save_graph(self.graph, filename)

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

    def edge_attribute_manager(self) -> og.AttributeManager:
        return self.graph.edge_attribute_manager()
