from opengeodeweb_microservice.schemas import Route, load_schema
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class Ping(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    pass


@dataclass
class PingResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    message: str


ping_route = Route(
    schema=load_schema(__file__),
    params=Ping,
    response=PingResponse,
)

__all__ = ["Ping", "PingResponse", "ping_route"]
