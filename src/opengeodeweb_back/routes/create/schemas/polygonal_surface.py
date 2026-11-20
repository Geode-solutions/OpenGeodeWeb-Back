from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Any, Optional, List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List, Any


@dataclass
class PolygonalSurface(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    name: str
    points: List[Any]
    polygons: List[List[int]]


@dataclass
class PolygonalSurfaceResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_id: Any
    geode_object_type: Any
    id: Any
    is_viewable: bool
    name: str
    native_file: str
    viewer_object_type: Any
    binary_light_viewable: Optional[str] = None
    collection_components: Optional[List[Any]] = None
    crs: Any
    mesh_components: Optional[List[Any]] = None
    nb_vertices: Optional[int] = None
    viewable_file: Optional[str] = None


polygonal_surface_route = Route(
    schema=load_schema(Path(__file__)),
    params=PolygonalSurface,
    response=PolygonalSurfaceResponse,
)

__all__ = ["PolygonalSurface", "PolygonalSurfaceResponse", "polygonal_surface_route"]
