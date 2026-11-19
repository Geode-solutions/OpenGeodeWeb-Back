from opengeodeweb_microservice.schema_types import AttributeName, DataId, GeodeId
from opengeodeweb_back.schema_types import AttributeInfo
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class ModelComponentVertexAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    component_ids: List[GeodeId]
    id: DataId


@dataclass
class ModelComponentVertexAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[AttributeInfo]


model_component_vertex_attribute_names_route = Route(
    schema=load_schema(Path(__file__)),
    params=ModelComponentVertexAttributeNames,
    response=ModelComponentVertexAttributeNamesResponse,
)

__all__ = ["ModelComponentVertexAttributeNames", "ModelComponentVertexAttributeNamesResponse", "model_component_vertex_attribute_names_route"]
