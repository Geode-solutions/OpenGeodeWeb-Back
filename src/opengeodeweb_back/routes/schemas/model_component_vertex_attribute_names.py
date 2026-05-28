from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class ModelComponentVertexAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    component_id: str
    id: str
