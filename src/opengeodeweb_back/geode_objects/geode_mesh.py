# Standard library imports
from __future__ import annotations
from abc import abstractmethod

# Third party imports
import opengeode as og

# Local application imports
from .types import GeodeObjectType, ViewerType
from .geode_object import GeodeObject


class GeodeMesh(GeodeObject):
    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "mesh"

    @abstractmethod
    def vertex_attribute_manager(self) -> og.AttributeManager: ...
