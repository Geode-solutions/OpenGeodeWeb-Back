from dataclasses import dataclass


@dataclass
class MissingFiles:
    filename: str
    input_geode_object: str
