from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import List

@dataclass
class PointXYZ(DataClassJsonMixin):
    x: float
    y: float
    z: float

@dataclass
class PointSet(DataClassJsonMixin):
    name: str
    points: List[PointXYZ]
