from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class CreatePoint(DataClassJsonMixin):
    def __post_init__(self):
        print(self, flush=True)

    name: str
    x: float
    y: float
    z: float
