from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class Delete(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


@dataclass
class DeleteResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


delete_route = Route(
    schema=load_schema(Path(__file__)),
    params=Delete,
    response=DeleteResponse,
)

__all__ = ["Delete", "DeleteResponse", "delete_route"]
