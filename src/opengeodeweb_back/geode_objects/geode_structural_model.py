# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode_geosciences as og_geosciences

# Local application imports
from .geode_brep import GeodeBRep

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import GeodeModelType


class GeodeStructuralModel(GeodeBRep):
    structural_model: og_geosciences.StructuralModel

    def __init__(
        self, structural_model: og_geosciences.StructuralModel | None = None
    ) -> None:
        self.structural_model = (
            structural_model
            if structural_model is not None
            else og_geosciences.StructuralModel()
        )
        super().__init__(self.structural_model)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "StructuralModel"

    @override
    def native_extension(self) -> str:
        return self.structural_model.native_extension()

    @override
    def builder(self) -> og_geosciences.StructuralModelBuilder:
        return og_geosciences.StructuralModelBuilder(self.structural_model)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeStructuralModel:
        return GeodeStructuralModel(og_geosciences.load_structural_model(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.structural_model_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_structural_model_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.StructuralModelInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.StructuralModelOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.structural_model_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_structural_model_saveable(
            self.structural_model, filename
        )

    @override
    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_structural_model(self.structural_model, filename)

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_structural_model(
            self.structural_model, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_structural_model(
            self.structural_model, filename_without_extension
        )

    def component_name(self, component_id: og.uuid) -> str | None:
        return self.structural_model.structural_model_component(component_id).name()

    @override
    def component(self, component_id: og.uuid) -> og.Component3D:
        return self.structural_model.structural_model_component(component_id)
