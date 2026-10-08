from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class ModelComponentPolygonAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    component_ids: List[str]
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
    time_steps: List[float]


@dataclass
class ModelComponentPolygonAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[Attribute]


model_component_polygon_attribute_names_route = Route(
    schema=load_schema(Path(__file__)),
    params=ModelComponentPolygonAttributeNames,
    response=ModelComponentPolygonAttributeNamesResponse,
)

__all__ = ["ModelComponentPolygonAttributeNames", "ModelComponentPolygonAttributeNamesResponse", "model_component_polygon_attribute_names_route"]
