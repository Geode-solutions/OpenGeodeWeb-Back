from opengeodeweb_microservice.schema_types import AttributeName, DataId
from opengeodeweb_back.schema_types import AttributeInfo
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class PolyhedronAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: DataId


@dataclass
class PolyhedronAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[AttributeInfo]


polyhedron_attribute_names_route = Route(
    schema=load_schema(Path(__file__)),
    params=PolyhedronAttributeNames,
    response=PolyhedronAttributeNamesResponse,
)

__all__ = ["PolyhedronAttributeNames", "PolyhedronAttributeNamesResponse", "polyhedron_attribute_names_route"]
