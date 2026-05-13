from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import List


@dataclass
class EdgedCurvePoint(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    x: float
    y: float
    z: float


@dataclass
class EdgedCurve(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    edges: List[List[int]]
    name: str
    points: List[EdgedCurvePoint]
