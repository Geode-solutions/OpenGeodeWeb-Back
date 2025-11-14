from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class VtmComponentIndices(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    id: str
