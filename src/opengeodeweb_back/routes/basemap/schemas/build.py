from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Any, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional


@dataclass
class Bounds(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x_max: float
    x_min: float
    y_max: float
    y_min: float


class Map(Enum):
    PLAN = "plan"
    ROUTES = "routes"
    SATELLITE = "satellite"


@dataclass
class Build(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    bounds: Bounds
    crs: Any
    maps: List[Map]
    z: float
    margin: Optional[bool] = None
    max_pixels: Optional[int] = None


@dataclass
class MeshBounds(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x_max: float
    x_min: float
    y_max: float
    y_min: float


@dataclass
class MapElement(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    map: str
    sources: List[str]


@dataclass
class BuildResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribution: str
    bounds: MeshBounds
    columns: int
    geode_id: Any
    geode_object_type: Any
    id: Any
    is_viewable: bool
    maps: List[MapElement]
    name: str
    native_file: str
    rows: int
    viewer_object_type: Any
    zoom: int
    binary_light_viewable: Optional[str] = None
    crs: Any
    nb_vertices: Optional[int] = None
    viewable_file: Optional[str] = None


build_route = Route(
    schema=load_schema(Path(__file__)),
    params=Build,
    response=BuildResponse,
)

__all__ = ["Bounds", "Build", "BuildResponse", "build_route"]
