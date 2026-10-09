from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class Element(Enum):
    CELL = "cell"
    EDGE = "edge"
    POLYGON = "polygon"
    POLYHEDRON = "polyhedron"
    VERTEX = "vertex"


@dataclass
class AttributeRange(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribute_name: str
    element: Element
    id: str
    component_ids: Optional[List[str]] = None


@dataclass
class AttributeRangeResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    max_values: List[float]
    min_values: List[float]
    no_data: bool


attribute_range_route = Route(
    schema=load_schema(Path(__file__)),
    params=AttributeRange,
    response=AttributeRangeResponse,
)

__all__ = ["AttributeRange", "AttributeRangeResponse", "attribute_range_route"]
