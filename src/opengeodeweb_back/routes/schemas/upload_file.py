from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadFile(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    filename: Optional[str] = None
