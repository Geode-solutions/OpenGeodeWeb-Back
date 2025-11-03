from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExportProject(DataClassJsonMixin):
    filename: str
    snapshot: Dict[str, Any]
