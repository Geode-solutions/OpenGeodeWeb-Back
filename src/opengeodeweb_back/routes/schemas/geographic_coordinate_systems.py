from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class GeographicCoordinateSystems(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    geode_object_type: str
