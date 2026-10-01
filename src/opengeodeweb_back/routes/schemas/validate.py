from opengeodeweb_microservice.schemas import Route, load_schema
from typing import List
from dataclasses_json import DataClassJsonMixin
from opengeodeweb_microservice.schemas import print_dataclass
from dataclasses import dataclass


@dataclass
class Validate(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    id: str


@dataclass
class ValidateResponse(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print_dataclass(self)

    is_valid: bool
    issues: List[str]
    nb_issues: int


validate_route = Route(
    schema=load_schema(__file__),
    params=Validate,
    response=ValidateResponse,
)

__all__ = ["Validate", "ValidateResponse", "validate_route"]
