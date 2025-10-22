from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class VtmComponentIndices(DataClassJsonMixin):
    id: str
