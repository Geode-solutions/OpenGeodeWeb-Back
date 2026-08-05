from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import List


@dataclass
class ModelComponentVertexAttributeNames(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    component_ids: List[str]
    id: str
