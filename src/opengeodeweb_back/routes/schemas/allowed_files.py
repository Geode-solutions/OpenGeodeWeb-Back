from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class AllowedFiles(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    pass


@dataclass
class AllowedFilesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    extensions: List[str]


allowed_files_route = Route(
    schema=load_schema(Path(__file__)),
    params=AllowedFiles,
    response=AllowedFilesResponse,
)

__all__ = ["AllowedFiles", "AllowedFilesResponse", "allowed_files_route"]
