from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Any, Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Optional, Any, List


@dataclass
class SourcePoint(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x: float
    y: float
    picked: Optional[bool] = None


@dataclass
class TargetPoint(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x: float
    y: float


@dataclass
class Align(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    id: Any
    name: str
    source_points: List[SourcePoint]
    target_points: List[TargetPoint]
    linked_ids: Optional[List[Any]] = None


@dataclass
class Linked(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any
    binary_light_viewable: Optional[str] = None
    crs: Any


@dataclass
class AlignResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    binary_light_viewable: Optional[str] = None
    crs: Any
    linked: Optional[List[Linked]] = None


align_route = Route(
    schema=load_schema(Path(__file__)),
    params=Align,
    response=AlignResponse,
)

__all__ = ["SourcePoint", "TargetPoint", "Align", "AlignResponse", "align_route"]
