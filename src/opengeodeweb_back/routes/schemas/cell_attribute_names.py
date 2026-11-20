from pathlib import Path
from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List, Any
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass
from typing import Any


@dataclass
class CellAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: Any


@dataclass
class CellAttributeNamesResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    attributes: List[Any]


cell_attribute_names_route = Route(
    schema=load_schema(Path(__file__)),
    params=CellAttributeNames,
    response=CellAttributeNamesResponse,
)

__all__ = ["CellAttributeNames", "CellAttributeNamesResponse", "cell_attribute_names_route"]
