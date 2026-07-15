# Standard library imports
from __future__ import annotations
from typing import Any

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
from opengeodeweb_microservice.database.data_types import GeodeModelType

# Local application imports
from .geode_model import GeodeModel, ComponentRegistry


class GeodeHorizonStack3D(GeodeModel):
    horizon_stack: og_geosciences.HorizonsStack3D

    def __init__(
        self, horizon_stack: og_geosciences.HorizonsStack3D | None = None
    ) -> None:
        self.horizon_stack = (
            horizon_stack
            if horizon_stack is not None
            else og_geosciences.HorizonsStack3D()
        )
        super().__init__(self.horizon_stack)

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "HorizonStack3D"

    def native_extension(self) -> str:
        return self.horizon_stack.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return False  
    def builder(self) -> og_geosciences.HorizonsStackBuilder3D:
        return og_geosciences.HorizonsStackBuilder3D(self.horizon_stack)

    @classmethod
    def load(cls, filename: str) -> GeodeHorizonStack3D:
        return GeodeHorizonStack3D(og_geosciences.load_horizons_stack3D(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        if hasattr(og_geosciences, "horizons_stack_additional_files3D"):
            return og_geosciences.horizons_stack_additional_files3D(filename)
        return []  # type: ignore

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        if hasattr(og_geosciences, "is_horizons_stack_loadable3D"):
            return og_geosciences.is_horizons_stack_loadable3D(filename)
        return 0  # type: ignore

    @classmethod
    def input_extensions(cls) -> list[str]:
        if hasattr(og_geosciences, "HorizonsStackInputFactory3D"):
            return og_geosciences.HorizonsStackInputFactory3D.list_creators()
        return []

    @classmethod
    def output_extensions(cls) -> list[str]:
        if hasattr(og_geosciences, "HorizonsStackOutputFactory3D"):
            return og_geosciences.HorizonsStackOutputFactory3D.list_creators()
        return []

    @classmethod
    def object_priority(cls, filename: str) -> int:
        if hasattr(og_geosciences, "horizons_stack_object_priority3D"):
            return og_geosciences.horizons_stack_object_priority3D(filename)
        return 0

    def is_saveable(self, filename: str) -> bool:
        if hasattr(og_geosciences, "is_horizons_stack_saveable3D"):
            return bool(og_geosciences.is_horizons_stack_saveable3D(
                self.horizon_stack, filename
            ))
        return True

    def save(self, filename: str) -> list[str]:
        if hasattr(og_geosciences, "save_horizons_stack3D"):
            return og_geosciences.save_horizons_stack3D(self.horizon_stack, filename)
        return []

    def save_viewable(self, filename_without_extension: str) -> str:
        return ""

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return ""

    def mesh_components(self) -> ComponentRegistry:
        return {}

    def collection_components(self) -> ComponentRegistry:
        return {}

    def boundaries(self, id: og.uuid) -> list[og.ComponentID]:
        return []

    def internals(self, id: og.uuid) -> list[og.ComponentID]:
        return []

    def items(self, id: og.uuid) -> list[og.ComponentID]:
        return []

    def component(self, id: og.uuid) -> og.Component3D:
        return None  # type: ignore

    def inspect(self) -> Any:
        return None

    def validate(self) -> Any:
        return None
