from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass


@dataclass
class ImportProject(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    pass
