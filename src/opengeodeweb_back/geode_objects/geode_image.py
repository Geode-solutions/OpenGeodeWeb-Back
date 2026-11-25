# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

# Third party imports
# Local application imports
from .geode_object import GeodeObject

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import ViewerObjectType


class GeodeImage(GeodeObject):
    @override
    @classmethod
    def viewer_object_type(cls) -> ViewerObjectType:
        return "image"
