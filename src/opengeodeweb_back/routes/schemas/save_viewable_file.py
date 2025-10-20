from dataclasses import dataclass


@dataclass
class SaveViewableFile:
    filename: str
    input_geode_object: str
