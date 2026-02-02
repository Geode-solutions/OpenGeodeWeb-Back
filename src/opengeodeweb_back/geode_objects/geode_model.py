# Standard library imports
from __future__ import annotations
from abc import abstractmethod

# Third party imports
import opengeode as og

# Local application imports
from .types import ViewerType, ViewerElementsType
from .geode_object import GeodeObject

ComponentRegistry = dict[og.ComponentType, list[og.uuid]]


class GeodeModel(GeodeObject):
    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "model"

    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "default"

    @abstractmethod
    def mesh_components(self) -> ComponentRegistry: ...
