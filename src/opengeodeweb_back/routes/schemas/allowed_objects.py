from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Dict, List, Any
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any


@dataclass
class AllowedObjects(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: Any


@dataclass
class AllowedObject(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    is_loadable: float
    loadable_family: str
    object_priority: int


@dataclass
class AllowedObjectsResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    allowed_objects: Dict[str, AllowedObject]
    objects_to_load: List[Any]


allowed_objects_route = Route(
    schema=load_schema(Path(__file__)),
    params=AllowedObjects,
    response=AllowedObjectsResponse,
)

__all__ = ["AllowedObjects", "AllowedObjectsResponse", "allowed_objects_route"]
