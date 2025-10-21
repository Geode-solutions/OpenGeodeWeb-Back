from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class AllowedFiles(DataClassJsonMixin):
    supported_feature: Optional[str] = None
