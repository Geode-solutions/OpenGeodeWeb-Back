from opengeodeweb_microservice.schema_types import DataId, Filename, GeodeId, ViewerId
from opengeodeweb_microservice.database.data_types import GeodeObjectType, ViewerObjectType
from opengeodeweb_back.schema_types import CRS, CollectionComponent, MeshComponent
from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class SaveViewableFile(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: Filename
    geode_object_type: GeodeObjectType


@dataclass
class SaveViewableFileItem(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    geode_id: GeodeId
    geode_object_type: GeodeObjectType
    id: DataId
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


@dataclass
class SaveViewableFileResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    data: List[SaveViewableFileItem]


save_viewable_file_route = Route(
    schema=load_schema(Path(__file__)),
    params=SaveViewableFile,
    response=SaveViewableFileResponse,
)

__all__ = ["SaveViewableFile", "SaveViewableFileResponse", "save_viewable_file_route"]
