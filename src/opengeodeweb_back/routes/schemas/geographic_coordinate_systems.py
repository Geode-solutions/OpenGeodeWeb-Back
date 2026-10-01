from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class GeographicCoordinateSystems(DataClassJsonMixin):
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
class GeographicCoordinateSystemsResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs_list: List[CRSList]


geographic_coordinate_systems_route = Route(
    schema=load_schema(__file__),
    params=GeographicCoordinateSystems,
    response=GeographicCoordinateSystemsResponse,
)

__all__ = ["GeographicCoordinateSystems", "GeographicCoordinateSystemsResponse", "geographic_coordinate_systems_route"]
