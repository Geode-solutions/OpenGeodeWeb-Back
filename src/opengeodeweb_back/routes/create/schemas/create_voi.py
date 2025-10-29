from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateVoi(DataClassJsonMixin):
    name: str
    """Name of the VOI"""

    aoi_id: str
    """ID of the corresponding AOI from which to take X and Y coordinates"""

    z_min: float
    """Minimum Z coordinate for the VOI"""

    z_max: float
    """Maximum Z coordinate for the VOI"""

    id: Optional[str] = None