from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class CreatePoint(DataClassJsonMixin):
    name: str
    x: float
    y: float
    z: float
