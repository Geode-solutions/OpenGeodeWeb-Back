from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ConvertGeographic(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: str
    name: str
    linked_ids: Optional[List[str]] = None


@dataclass
class ConvertGeographicResponseCRS(DataClassJsonMixin):
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
    binary_light_viewable: Optional[str] = None
    crs: Optional[LinkedCRS] = None


@dataclass
class ConvertGeographicResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    binary_light_viewable: Optional[str] = None
    crs: Optional[ConvertGeographicResponseCRS] = None
    linked: Optional[List[Linked]] = None


convert_geographic_route = Route(
    schema=load_schema(Path(__file__)),
    params=ConvertGeographic,
    response=ConvertGeographicResponse,
)

__all__ = ["ConvertGeographic", "ConvertGeographicResponse", "convert_geographic_route"]
