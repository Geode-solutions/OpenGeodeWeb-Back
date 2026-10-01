from opengeodeweb_microservice.schemas import Route, load_schema
from typing import Dict, Any
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class ImportProject(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    pass


@dataclass
class ImportProjectResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    snapshot: Dict[str, Any]


import_project_route = Route(
    schema=load_schema(__file__),
    params=ImportProject,
    response=ImportProjectResponse,
)

__all__ = ["ImportProject", "ImportProjectResponse", "import_project_route"]
