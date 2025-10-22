from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class TextureCoordinates(DataClassJsonMixin):
    id: str
