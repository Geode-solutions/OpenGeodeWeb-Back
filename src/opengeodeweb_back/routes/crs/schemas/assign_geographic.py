from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AssignGeographic(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: str
    name: str
    linked_ids: Optional[List[str]] = None


@dataclass
class AssignGeographicResponseCRS(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


@dataclass
class LinkedCRS(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


@dataclass
class Linked(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str
    crs: Optional[LinkedCRS] = None
    implausible: Optional[bool] = None


@dataclass
class AssignGeographicResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs: Optional[AssignGeographicResponseCRS] = None
    implausible: Optional[bool] = None
    linked: Optional[List[Linked]] = None


assign_geographic_route = Route(
    schema=load_schema(Path(__file__)),
    params=AssignGeographic,
    response=AssignGeographicResponse,
)

__all__ = ["AssignGeographic", "AssignGeographicResponse", "assign_geographic_route"]
