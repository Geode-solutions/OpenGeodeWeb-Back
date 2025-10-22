from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class GeographicCoordinateSystems(DataClassJsonMixin):
    input_geode_object: str
