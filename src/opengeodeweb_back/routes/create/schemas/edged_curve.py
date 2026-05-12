from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import List


@dataclass
class Point(DataClassJsonMixin):
    x: float
    y: float
    z: float


@dataclass
class EdgedCurve(DataClassJsonMixin):
    name: str
    points: List[Point]
    edges: List[List[int]]
