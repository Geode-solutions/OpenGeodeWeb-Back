from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class TimeSeriesMissingFiles(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: str


@dataclass
class TimeSeriesMissingFilesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    additional_files: List[str]
    has_missing_files: bool
    mandatory_files: List[str]


time_series_missing_files_route = Route(
    schema=load_schema(Path(__file__)),
    params=TimeSeriesMissingFiles,
    response=TimeSeriesMissingFilesResponse,
)

__all__ = ["TimeSeriesMissingFiles", "TimeSeriesMissingFilesResponse", "time_series_missing_files_route"]
