# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, Any, get_args, cast

# Third party imports
import opengeode as og

# Local application imports
from .types import GeodeObjectType, GeodeMeshType, ViewerType
from .geode_object import GeodeObject


class GeodeMesh(GeodeObject):
    @classmethod
    def load(cls, filename: str) -> GeodeObject:
        return cls.load_mesh(filename)

    @classmethod
    @abstractmethod
    def load_mesh(cls, filename: str) -> GeodeMesh: ...

    @classmethod
    def geode_object_type(cls) -> GeodeObjectType:
        return cls.geode_mesh_type()

    @classmethod
    @abstractmethod
    def geode_mesh_type(cls) -> GeodeMeshType: ...

    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "mesh"
