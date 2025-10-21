from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class MeshComponents(DataClassJsonMixin):
    id: str
