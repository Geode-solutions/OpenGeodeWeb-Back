from opengeodeweb_back.schema_types import AttributeName
from opengeodeweb_microservice.schema_types import DataId
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class PolygonAttributeRange(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribute_name: AttributeName
    id: DataId


@dataclass
class PolygonAttributeRangeResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    max_values: List[float]
    min_values: List[float]
    no_data: bool


polygon_attribute_range_route = Route(
    schema=load_schema(Path(__file__)),
    params=PolygonAttributeRange,
    response=PolygonAttributeRangeResponse,
)

__all__ = ["PolygonAttributeRange", "PolygonAttributeRangeResponse", "polygon_attribute_range_route"]
