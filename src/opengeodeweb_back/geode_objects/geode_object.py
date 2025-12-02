# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, Any, get_args, cast

# Third party imports
import opengeode as og

# Local application imports
from .types import GeodeObjectType, ViewerType


class GeodeObject(ABC):
    identifier: og.Identifier

    def __init__(self, identifier: og.Identifier | None = None) -> None:
        self.identifier = identifier if identifier is not None else og.Identifier()

    @classmethod
    @abstractmethod
    def geode_object_type(cls) -> GeodeObjectType: ...

    @classmethod
    @abstractmethod
    def viewer_type(cls) -> ViewerType: ...

    @classmethod
    @abstractmethod
    def is_3D(cls) -> bool: ...

    @classmethod
    @abstractmethod
    def is_viewable(cls) -> bool: ...

    @abstractmethod
    def builder(self) -> Any: ...

    @classmethod
    @abstractmethod
    def is_loadable(cls, filename: str) -> og.Percentage: ...

    @classmethod
    @abstractmethod
    def load(cls, filename: str) -> GeodeObject: ...

    @classmethod
    @abstractmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles: ...

    @abstractmethod
    def native_extension(cls) -> str: ...

    @classmethod
    @abstractmethod
    def input_extensions(cls) -> list[str]: ...

    @classmethod
    @abstractmethod
    def object_priority(cls, filename: str) -> int: ...

    @classmethod
    @abstractmethod
    def output_extensions(cls) -> list[str]: ...

    @abstractmethod
    def is_saveable(self, filename: str) -> bool: ...

    @abstractmethod
    def save(self, filename: str) -> list[str]: ...

    @abstractmethod
    def save_viewable(self, filename_without_extension: str) -> str: ...

    @abstractmethod
    def save_light_viewable(self, filename_without_extension: str) -> str: ...

    @abstractmethod
    def inspect(self) -> Any: ...
