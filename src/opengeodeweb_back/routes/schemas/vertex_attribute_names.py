from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Any
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any


@dataclass
class VertexAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any


@dataclass
class VertexAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[Any]


vertex_attribute_names_route = Route(
    schema=load_schema(Path(__file__)),
    params=VertexAttributeNames,
    response=VertexAttributeNamesResponse,
)

__all__ = ["VertexAttributeNames", "VertexAttributeNamesResponse", "vertex_attribute_names_route"]
