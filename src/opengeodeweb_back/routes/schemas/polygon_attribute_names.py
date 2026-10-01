from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class PolygonAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


@dataclass
class Attribute(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribute_id: str
    attribute_name: str
    max_value: float
    max_values: List[float]
    min_value: float
    min_values: List[float]
    nb_items: int
    no_data: bool


@dataclass
class PolygonAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[Attribute]


polygon_attribute_names_route = Route(
    schema=load_schema(__file__),
    params=PolygonAttributeNames,
    response=PolygonAttributeNamesResponse,
)

__all__ = ["PolygonAttributeNames", "PolygonAttributeNamesResponse", "polygon_attribute_names_route"]
