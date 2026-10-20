from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class ModelComponentPolyhedronAttributeRange(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribute_name: str
    component_ids: List[str]
    id: str


@dataclass
class ModelComponentPolyhedronAttributeRangeResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    max_values: List[float]
    min_values: List[float]
    no_data: bool


model_component_polyhedron_attribute_range_route = Route(
    schema=load_schema(Path(__file__)),
    params=ModelComponentPolyhedronAttributeRange,
    response=ModelComponentPolyhedronAttributeRangeResponse,
)

__all__ = ["ModelComponentPolyhedronAttributeRange", "ModelComponentPolyhedronAttributeRangeResponse", "model_component_polyhedron_attribute_range_route"]
