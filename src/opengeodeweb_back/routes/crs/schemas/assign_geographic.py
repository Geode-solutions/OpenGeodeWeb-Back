from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Any, Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class AssignGeographic(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: Any
    name: str
    linked_ids: Optional[List[Any]] = None
    only_plausible: Optional[bool] = None


@dataclass
class Linked(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any
    crs: Any
    implausible: Optional[bool] = None


@dataclass
class AssignGeographicResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs: Any
    implausible: Optional[bool] = None
    linked: Optional[List[Linked]] = None


assign_geographic_route = Route(
    schema=load_schema(Path(__file__)),
    params=AssignGeographic,
    response=AssignGeographicResponse,
)

__all__ = ["AssignGeographic", "AssignGeographicResponse", "assign_geographic_route"]
