from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any


@dataclass
class Active(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any


@dataclass
class ActiveResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    crs_name: str
    crs_info: Any


active_route = Route(
    schema=load_schema(Path(__file__)),
    params=Active,
    response=ActiveResponse,
)

__all__ = ["Active", "ActiveResponse", "active_route"]
