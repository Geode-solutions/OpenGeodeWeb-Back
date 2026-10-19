from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class DataMissingFiles(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: str
    geode_object_type: str


@dataclass
class DataMissingFilesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    additional_files: List[str]
    has_missing_files: bool
    mandatory_files: List[str]


data_missing_files_route = Route(
    schema=load_schema(Path(__file__)),
    params=DataMissingFiles,
    response=DataMissingFilesResponse,
)

__all__ = ["DataMissingFiles", "DataMissingFilesResponse", "data_missing_files_route"]
