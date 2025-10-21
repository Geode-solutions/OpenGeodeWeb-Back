from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class PolyhedronAttributeNames(DataClassJsonMixin):
    id: str
