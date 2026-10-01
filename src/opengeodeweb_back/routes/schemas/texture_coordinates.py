from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class TextureCoordinates(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


@dataclass
class TextureCoordinatesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    texture_coordinates: List[str]


texture_coordinates_route = Route(
    schema=load_schema(__file__),
    params=TextureCoordinates,
    response=TextureCoordinatesResponse,
)

__all__ = ["TextureCoordinates", "TextureCoordinatesResponse", "texture_coordinates_route"]
