from dataclasses import dataclass


@dataclass
class CreatePoint:
    name: str
    x: float
    y: float
    z: float
