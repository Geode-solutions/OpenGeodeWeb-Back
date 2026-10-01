from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class GeodeObjectInheritance(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_object_type: str


@dataclass
class GeodeObjectInheritanceResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    children: List[str]
    parents: List[str]


geode_object_inheritance_route = Route(
    schema=load_schema(__file__),
    params=GeodeObjectInheritance,
    response=GeodeObjectInheritanceResponse,
)

__all__ = ["GeodeObjectInheritance", "GeodeObjectInheritanceResponse", "geode_object_inheritance_route"]
