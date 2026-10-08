from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadFile(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    filename: Optional[str] = None


@dataclass
class UploadFileResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    message: str


upload_file_route = Route(
    schema=load_schema(Path(__file__)),
    params=UploadFile,
    response=UploadFileResponse,
)

__all__ = ["UploadFile", "UploadFileResponse", "upload_file_route"]
