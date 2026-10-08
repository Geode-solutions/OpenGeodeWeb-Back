from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class Kill(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    pass


@dataclass
class KillResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    message: str


kill_route = Route(
    schema=load_schema(Path(__file__)),
    params=Kill,
    response=KillResponse,
)

__all__ = ["Kill", "KillResponse", "kill_route"]
