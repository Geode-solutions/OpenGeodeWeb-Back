from opengeodeweb_microservice.database.data_types import GeodeObjectType, ViewerObjectType
from opengeodeweb_back.schema_types import CRS, CollectionComponent, MeshComponent
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import List


@dataclass
class HorizonStack(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    horizons: List[str]
    name: str
    unit_names: List[str]


@dataclass
class HorizonStackResponse(DataClassJsonMixin):
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


horizon_stack_route = Route(
    schema=load_schema(Path(__file__)),
    params=HorizonStack,
    response=HorizonStackResponse,
)

__all__ = ["HorizonStack", "HorizonStackResponse", "horizon_stack_route"]
