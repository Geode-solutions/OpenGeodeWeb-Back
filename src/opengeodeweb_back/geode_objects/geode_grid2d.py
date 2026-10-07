# Standard library imports
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, override

# Third party imports
import opengeode_inspector as og_inspector

# Local application imports
from .geode_mesh import GeodeMesh

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import ViewerElementsType


class GeodeGrid2D(GeodeMesh):
    @override
    @classmethod
    def is_3d(cls) -> bool:
        return False

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "polygons"

    @override
    def inspect(self) -> object:
        return None

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.ObjectValidity()

    @abstractmethod
    def cell_attribute_manager(self) -> og.AttributeManager: ...
