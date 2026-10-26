from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class AssignGeographic(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: str
    name: str


@dataclass
class CRS(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


@dataclass
class AssignGeographicResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs: Optional[CRS] = None
    implausible: Optional[bool] = None


assign_geographic_route = Route(
    schema=load_schema(Path(__file__)),
    params=AssignGeographic,
    response=AssignGeographicResponse,
)

__all__ = ["AssignGeographic", "AssignGeographicResponse", "assign_geographic_route"]
