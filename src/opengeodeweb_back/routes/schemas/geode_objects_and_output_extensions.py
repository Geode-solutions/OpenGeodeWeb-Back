from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class GeodeObjectsAndOutputExtensions(DataClassJsonMixin):
    filename: str
    input_geode_object: str
