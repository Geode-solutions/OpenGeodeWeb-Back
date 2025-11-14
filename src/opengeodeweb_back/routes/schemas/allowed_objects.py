from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class AllowedObjects(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    filename: str
    supported_feature: Optional[str] = None
