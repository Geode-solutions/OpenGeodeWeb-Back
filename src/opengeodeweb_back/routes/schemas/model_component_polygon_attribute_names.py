from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class ModelComponentPolygonAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    component_id: str
    id: str
