from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class MissingFiles(DataClassJsonMixin):
    filename: str
    input_geode_object: str
