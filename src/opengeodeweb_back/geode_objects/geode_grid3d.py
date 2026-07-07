# Standard library imports
from __future__ import annotations
from abc import abstractmethod

# Third party imports
import opengeode as og
import opengeode_inspector as og_inspector
from opengeodeweb_microservice.database.data_types import ViewerElementsType

# Local application imports
from .geode_mesh import GeodeMesh


class GeodeGrid3D(GeodeMesh):
    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "polyhedra"

    def builder(self) -> object:
        return None

    def inspect(self) -> object:
        return None

    def validate(self) -> og_inspector.ObjectValidity:
        result=og_inspector.ObjectValidity()
        return result

    @abstractmethod
    def cell_attribute_manager(self) -> og.AttributeManager: ...
