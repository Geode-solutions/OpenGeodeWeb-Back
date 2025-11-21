# Standard library imports
from __future__ import annotations

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

    def builder(self) -> None:
        return None

    def inspect(self) -> None:
        return None
