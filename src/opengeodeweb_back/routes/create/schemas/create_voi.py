from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateVoi(DataClassJsonMixin):
    def __post_init__(self) -> None:
        print(self, flush=True)

    aoi_id: str
    """ID of the corresponding AOI"""

    name: str
    """Name of the VOI"""

    z_max: float
    """Maximum Z coordinate"""

    z_min: float
    """Minimum Z coordinate"""

    id: Optional[str] = None
    """Optional ID for updating existing VOI"""
