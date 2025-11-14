from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class TextureCoordinates(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    id: str
