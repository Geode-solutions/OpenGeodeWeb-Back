# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_vertex_set import GeodeVertexSet


class GeodeGraph(GeodeVertexSet):
    graph: og.Graph

    def __init__(self, graph: og.Graph | None = None) -> None:
        self.graph = graph if graph is not None else og.Graph.create()
        super().__init__(self.graph)

    @classmethod
    def geode_object_type(cls) -> GeodeMeshType:
        return "Graph"

    def native_extension(self) -> str:
        return self.graph.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return False

    @classmethod
    def is_viewable(cls) -> bool:
        return False

    def builder(self) -> og.GraphBuilder:
        return og.GraphBuilder.create(self.graph)

    @classmethod
    def load(cls, filename: str) -> GeodeGraph:
        return GeodeGraph(og.load_graph(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.graph_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_graph_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.GraphInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.GraphOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.graph_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_graph_saveable(self.graph, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_graph(self.graph, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return ""

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return ""

    def inspect(self) -> object:
        return None
