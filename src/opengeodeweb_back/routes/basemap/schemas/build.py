from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


@dataclass
class Bounds(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x_max: float
    x_min: float
    y_max: float
    y_min: float


@dataclass
class CRSParams(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


class Map(Enum):
    PLAN = "plan"
    ROUTES = "routes"
    SATELLITE = "satellite"


@dataclass
class Build(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    bounds: Bounds
    crs: CRSParams
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
class CollectionComponent(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_id: str
    is_active: bool
    items: List[str]
    name: str
    type: str


@dataclass
class CRS(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    authority: str
    code: str
    name: str


@dataclass
class MapElement(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    map: str
    sources: List[str]


@dataclass
class MeshComponent(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    boundaries: List[str]
    geode_id: str
    internals: List[str]
    is_active: bool
    name: str
    type: str
    viewer_id: int


@dataclass
class BuildResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attribution: str
    bounds: MeshBounds
    columns: int
    geode_id: str
    geode_object_type: str
    id: str
    is_viewable: bool
    maps: List[MapElement]
    name: str
    native_file: str
    rows: int
    tiles_folder: str
    viewer_type: str
    zoom: int
    binary_light_viewable: Optional[str] = None
    collection_components: Optional[List[CollectionComponent]] = None
    crs: Optional[CRS] = None
    mesh_components: Optional[List[MeshComponent]] = None
    nb_vertices: Optional[int] = None
    viewable_file: Optional[str] = None


build_route = Route(
    schema=load_schema(Path(__file__)),
    params=Build,
    response=BuildResponse,
)

__all__ = ["Bounds", "CRSParams", "Build", "BuildResponse", "build_route"]
