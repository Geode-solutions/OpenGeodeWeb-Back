# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, Any, get_args, cast

# Third party imports
import opengeode as og

# Local application imports
from .types import GeodeObjectType, GeodeModelType, ViewerType
from .geode_object import GeodeObject

ComponentRegistry = dict[og.ComponentType, list[og.uuid]]


class GeodeModel(GeodeObject):
    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "model"

    @abstractmethod
    def mesh_components(self) -> ComponentRegistry: ...
