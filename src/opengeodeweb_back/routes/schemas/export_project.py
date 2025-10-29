from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ExportProject(DataClassJsonMixin):
    snapshot: Dict[str, Any]
    filename: Optional[str] = None
