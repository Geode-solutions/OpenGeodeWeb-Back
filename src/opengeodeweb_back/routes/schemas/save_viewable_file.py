from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class SaveViewableFile(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    filename: str
    geode_object_type: str
