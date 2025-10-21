from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadFile(DataClassJsonMixin):
    filename: Optional[str] = None
