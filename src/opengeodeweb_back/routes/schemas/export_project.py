from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExportProject(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    filename: str
    snapshot: Dict[str, Any]
