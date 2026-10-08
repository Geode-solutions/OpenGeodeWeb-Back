# Standard library imports
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, override

# Third party imports
import opengeode as og

# Local application imports
from .geode_object import GeodeObject

if TYPE_CHECKING:
    from opengeodeweb_microservice.database.data_types import (
        ViewerElementsType,
        ViewerType,
    )

ComponentRegistry = dict[og.ComponentType, list[og.uuid]]


class GeodeModel(GeodeObject):
    @override
    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "model"

    @override
    @classmethod
    def viewer_elements_type(cls) -> ViewerElementsType:
        return "default"

    @abstractmethod
    def mesh_components(self) -> ComponentRegistry: ...

    @abstractmethod
    def collection_components(self) -> ComponentRegistry: ...

    @abstractmethod
    def boundaries(self, component_id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def internals(self, component_id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def items(self, component_id: og.uuid) -> list[og.ComponentID]: ...

    @abstractmethod
    def component(self, component_id: og.uuid) -> og.Component2D | og.Component3D: ...
