from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class Point(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    name: str
    x: float
    y: float
    z: float
