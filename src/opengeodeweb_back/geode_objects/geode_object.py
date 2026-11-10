# Standard library imports
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

# Third party imports
import opengeode as og

if TYPE_CHECKING:
    from collections.abc import Sequence

    import opengeode_inspector as og_inspector
    from opengeodeweb_microservice.database.data_types import (
        GeodeObjectType,
        ViewerElementsType,
        ViewerType,
    )

# Local application imports


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
    def viewer_elements_type(cls) -> ViewerElementsType: ...

    @classmethod
    @abstractmethod
    def is_3d(cls) -> bool: ...

    @classmethod
    @abstractmethod
    def is_viewable(cls) -> bool: ...

    @abstractmethod
    def builder(self) -> og.IdentifierBuilder: ...

    @classmethod
    @abstractmethod
    def is_loadable(cls, filename: str) -> og.Percentage: ...

    @classmethod
    @abstractmethod
    def load(cls, filename: str) -> Sequence[GeodeObject]: ...

    @classmethod
    def load_one(cls, filename: str) -> Self:
        objects = cls.load(filename)
        if len(objects) != 1:
            message = f"Expected exactly 1 object in {filename}, but {len(objects)} were loaded"
            raise ValueError(message)
        (geode_object,) = objects
        if not isinstance(geode_object, cls):
            message = f"Object loaded from {filename} is not a {cls.__name__}"
            raise TypeError(message)
        return geode_object

    @classmethod
    @abstractmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles: ...

    @abstractmethod
    def native_extension(self) -> str: ...

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
    def inspect(self) -> object: ...

    @abstractmethod
    def validate(self) -> og_inspector.ObjectValidity: ...
