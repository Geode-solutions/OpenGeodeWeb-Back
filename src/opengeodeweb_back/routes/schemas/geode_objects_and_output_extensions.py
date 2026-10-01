from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Dict
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class GeodeObjectsAndOutputExtensions(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: str
    geode_object_type: str


@dataclass
class GeodeObjectsAndOutputExtensionsResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_objects_and_output_extensions: Dict[str, Dict[str, bool]]


geode_objects_and_output_extensions_route = Route(
    schema=load_schema(__file__),
    params=GeodeObjectsAndOutputExtensions,
    response=GeodeObjectsAndOutputExtensionsResponse,
)

__all__ = ["GeodeObjectsAndOutputExtensions", "GeodeObjectsAndOutputExtensionsResponse", "geode_objects_and_output_extensions_route"]
