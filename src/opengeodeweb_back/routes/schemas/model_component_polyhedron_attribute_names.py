from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class ModelComponentPolyhedronAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    component_ids: list[str]
    id: str
