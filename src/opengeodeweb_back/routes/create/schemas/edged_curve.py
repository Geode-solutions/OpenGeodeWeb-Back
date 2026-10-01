from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class EdgedCurvePoint(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    x: float
    y: float
    z: float


@dataclass
class EdgedCurve(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    edges: List[List[int]]
    name: str
    points: List[EdgedCurvePoint]


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
class EdgedCurveResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_object_type: str
    id: str
    is_viewable: bool
    name: str
    native_file: str
    viewer_type: str
    binary_light_viewable: Optional[str] = None
    collection_components: Optional[List[CollectionComponent]] = None
    mesh_components: Optional[List[MeshComponent]] = None
    nb_vertices: Optional[int] = None
    viewable_file: Optional[str] = None


edged_curve_route = Route(
    schema=load_schema(__file__),
    params=EdgedCurve,
    response=EdgedCurveResponse,
)

__all__ = ["EdgedCurvePoint", "EdgedCurve", "EdgedCurveResponse", "edged_curve_route"]
