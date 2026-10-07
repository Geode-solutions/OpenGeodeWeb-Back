# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

# Third party imports
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector

# Local application imports
from .geode_model import ComponentRegistry, GeodeModel

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import GeodeModelType


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

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "HorizonStack3D"

    @override
    def native_extension(self) -> str:
        return self.horizon_stack.native_extension()

    @override
    @classmethod
    def is_3d(cls) -> bool:
        return True

    @override
    @classmethod
    def is_viewable(cls) -> bool:
        return False

    @override
    def builder(self) -> og_geosciences.HorizonsStackBuilder3D:
        return og_geosciences.HorizonsStackBuilder3D(self.horizon_stack)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeHorizonStack3D:
        return GeodeHorizonStack3D(og_geosciences.load_horizons_stack3D(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.horizons_stack_additional_files3D(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_horizons_stack_loadable3D(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.HorizonsStackInputFactory3D.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.HorizonsStackOutputFactory3D.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.horizons_stack_object_priority3D(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_horizons_stack_saveable3D(self.horizon_stack, filename)

    @override
    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_horizons_stack3D(self.horizon_stack, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return ""

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return ""

    @override
    def mesh_components(self) -> ComponentRegistry:
        return {}

    @override
    def collection_components(self) -> ComponentRegistry:
        return {}

    @override
    def boundaries(self, component_id: og.uuid) -> list[og.ComponentID]:
        return []

    @override
    def internals(self, component_id: og.uuid) -> list[og.ComponentID]:
        return []

    @override
    def items(self, component_id: og.uuid) -> list[og.ComponentID]:
        return []

    @override
    def component(self, component_id: og.uuid) -> og.Component3D:
        msg = "HorizonStack3D has no mesh components"
        raise NotImplementedError(msg)

    @override
    def inspect(self) -> None:
        return None

    @override
    def validate(self) -> og_inspector.ObjectValidity:
        return og_inspector.ObjectValidity()
