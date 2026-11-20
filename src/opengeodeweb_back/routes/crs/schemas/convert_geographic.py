from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Any, Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ConvertGeographic(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: Any
    name: str
    linked_ids: Optional[List[Any]] = None


@dataclass
class Linked(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any
    binary_light_viewable: Optional[str] = None
    crs: Any


@dataclass
class ConvertGeographicResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    binary_light_viewable: Optional[str] = None
    crs: Any
    linked: Optional[List[Linked]] = None


convert_geographic_route = Route(
    schema=load_schema(Path(__file__)),
    params=ConvertGeographic,
    response=ConvertGeographicResponse,
)

__all__ = ["ConvertGeographic", "ConvertGeographicResponse", "convert_geographic_route"]
