# Standard library imports
from __future__ import annotations
from abc import abstractmethod

# Third party imports
import opengeode as og
import geode_viewables as viewables

# Local application imports
from .types import GeodeMeshType
from .geode_mesh import GeodeMesh


class GeodeGrid3D(GeodeMesh):
    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> object:
        return None

    def inspect(self) -> object:
        return None

    @abstractmethod
    def cell_attribute_manager(self) -> og.AttributeManager: ...
