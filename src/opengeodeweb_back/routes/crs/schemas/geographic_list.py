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

    geode_object_type: str


@dataclass
class CRSList(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


@dataclass
class GeographicListResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs_list: List[CRSList]


geographic_list_route = Route(
    schema=load_schema(Path(__file__)),
    params=GeographicList,
    response=GeographicListResponse,
)

__all__ = ["GeographicList", "GeographicListResponse", "geographic_list_route"]
