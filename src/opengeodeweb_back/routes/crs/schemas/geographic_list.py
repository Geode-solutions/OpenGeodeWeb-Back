from opengeodeweb_microservice.database.data_types import GeodeObjectType
from opengeodeweb_back.schema_types import CRS
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class GeographicList(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_object_type: GeodeObjectType


@dataclass
class GeographicListResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs_list: List[CRS]


geographic_list_route = Route(
    schema=load_schema(Path(__file__)),
    params=GeographicList,
    response=GeographicListResponse,
)

__all__ = ["GeographicList", "GeographicListResponse", "geographic_list_route"]
