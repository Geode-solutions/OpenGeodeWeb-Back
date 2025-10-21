from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Point(DataClassJsonMixin):
    x: float
    y: float


@dataclass
class CreateAoi(DataClassJsonMixin):
    name: str
    """Name of the AOI"""

    points: List[Point]
    z: float
    id: Optional[str] = None
