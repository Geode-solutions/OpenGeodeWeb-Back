from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class AllowedObjects(DataClassJsonMixin):
    filename: str
    supported_feature: Optional[str] = None
