from dataclasses_json import DataClassJsonMixin
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateVoi(DataClassJsonMixin):
    aoi_id: str
    """ID of the corresponding AOI"""

    max_x: float
    """Maximum X coordinate from AOI"""

    max_y: float
    """Maximum Y coordinate from AOI"""

    min_x: float
    """Minimum X coordinate from AOI"""

    min_y: float
    """Minimum Y coordinate from AOI"""

    name: str
    """Name of the VOI"""

    z_max: float
    """Maximum Z coordinate"""

    z_min: float
    """Minimum Z coordinate"""

    id: Optional[str] = None
    """Optional ID for updating existing VOI"""
