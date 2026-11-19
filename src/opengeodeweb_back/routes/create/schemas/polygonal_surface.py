from opengeodeweb_microservice.database.data_types import GeodeObjectType, ViewerObjectType
from opengeodeweb_microservice.schema_types import Point3D
from opengeodeweb_back.schema_types import CRS, CollectionComponent, MeshComponent
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class PolygonalSurface(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    name: str
    points: List[Point3D]
    polygons: List[List[int]]


@dataclass
class PolygonalSurfaceResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_id: str
    geode_object_type: GeodeObjectType
    id: str
    is_viewable: bool
    name: str
    native_file: str
    viewer_object_type: ViewerObjectType
    binary_light_viewable: Optional[str] = None
    collection_components: Optional[List[CollectionComponent]] = None
    crs: Optional[CRS] = None
    mesh_components: Optional[List[MeshComponent]] = None
    nb_vertices: Optional[int] = None
    viewable_file: Optional[str] = None


polygonal_surface_route = Route(
    schema=load_schema(Path(__file__)),
    params=PolygonalSurface,
    response=PolygonalSurfaceResponse,
)

__all__ = ["Point3D", "PolygonalSurface", "PolygonalSurfaceResponse", "polygonal_surface_route"]
