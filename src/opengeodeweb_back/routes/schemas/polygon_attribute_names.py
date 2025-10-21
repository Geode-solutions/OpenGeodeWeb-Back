from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class PolygonAttributeNames(DataClassJsonMixin):
    id: str
