# Standard library imports
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, override

# Third party imports
# Local application imports
from .geode_object import GeodeObject

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import ViewerType


class GeodeMesh(GeodeObject):
    @override
    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "mesh"

    @abstractmethod
    def vertex_attribute_manager(self) -> og.AttributeManager: ...
