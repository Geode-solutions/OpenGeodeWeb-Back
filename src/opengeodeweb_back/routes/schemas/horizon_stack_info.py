from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class HorizonStackInfo(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


@dataclass
class Horizon(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str
    name: str


@dataclass
class Unit(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str
    name: str


@dataclass
class HorizonStackInfoResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    horizons: List[Horizon]
    units: List[Unit]


horizon_stack_info_route = Route(
    schema=load_schema(Path(__file__)),
    params=HorizonStackInfo,
    response=HorizonStackInfoResponse,
)

__all__ = ["HorizonStackInfo", "HorizonStackInfoResponse", "horizon_stack_info_route"]
