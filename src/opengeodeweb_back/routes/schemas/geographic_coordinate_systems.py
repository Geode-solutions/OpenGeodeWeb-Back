from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class GeographicCoordinateSystems(DataClassJsonMixin):
    def __post_init__(self):
        print(self, flush=True)

    input_geode_object: str
