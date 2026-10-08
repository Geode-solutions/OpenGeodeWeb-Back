from pathlib import Path
from opengeodeweb_microservice.schemas import BinaryResponse, Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExportProject(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: str
    snapshot: Dict[str, Any]


export_project_route = Route(
    schema=load_schema(Path(__file__)),
    params=ExportProject,
    response=BinaryResponse,
)

__all__ = ["ExportProject", "export_project_route"]
