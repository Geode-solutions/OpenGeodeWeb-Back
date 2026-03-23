# Standard library imports
from __future__ import annotations
from abc import abstractmethod
from typing import Union

# Third party imports
import opengeode as og
from opengeodeweb_microservice.database.data_types import ViewerType, ViewerElementsType

# Local application imports
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

    @abstractmethod
    def collection_components(self) -> ComponentRegistry: ...

    @abstractmethod
    def boundaries(self, id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def internals(self, id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def items(self, id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def component(self, id: og.uuid) -> og.Component2D | og.Component3D: ...
