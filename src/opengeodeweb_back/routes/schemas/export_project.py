from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class ExportProject(DataClassJsonMixin):
    filename: str
    snapshot: dict[str, object]
