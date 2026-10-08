# Standard library imports
from __future__ import annotations

from typing import TYPE_CHECKING, override

import geode_viewables as viewables

# Third party imports
import opengeode_geosciences as og_geosciences

# Local application imports
from .geode_structural_model import GeodeStructuralModel

if TYPE_CHECKING:
    import opengeode as og
    from opengeodeweb_microservice.database.data_types import GeodeModelType


class GeodeImplicitStructuralModel(GeodeStructuralModel):
    implicit_structural_model: og_geosciences.ImplicitStructuralModel

    def __init__(
        self,
        implicit_structural_model: og_geosciences.ImplicitStructuralModel | None = None,
    ) -> None:
        self.implicit_structural_model = (
            implicit_structural_model
            if implicit_structural_model is not None
            else og_geosciences.ImplicitStructuralModel()
        )
        super().__init__(self.implicit_structural_model)

    @override
    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "ImplicitStructuralModel"

    @override
    def native_extension(self) -> str:
        return self.implicit_structural_model.native_extension()

    @override
    def builder(self) -> og_geosciences.ImplicitStructuralModelBuilder:
        return og_geosciences.ImplicitStructuralModelBuilder(self.implicit_structural_model)

    @override
    @classmethod
    def load(cls, filename: str) -> GeodeImplicitStructuralModel:
        return GeodeImplicitStructuralModel(og_geosciences.load_implicit_structural_model(filename))

    @override
    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.implicit_structural_model_additional_files(filename)

    @override
    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_implicit_structural_model_loadable(filename)

    @override
    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitStructuralModelInputFactory.list_creators()

    @override
    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.ImplicitStructuralModelOutputFactory.list_creators()

    @override
    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.implicit_structural_model_object_priority(filename)

    @override
    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_implicit_structural_model_saveable(
            self.implicit_structural_model, filename
        )

    @override
    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_implicit_structural_model(
            self.implicit_structural_model, filename
        )

    @override
    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_implicit_structural_model(
            self.implicit_structural_model, filename_without_extension
        )

    @override
    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_implicit_structural_model(
            self.implicit_structural_model, filename_without_extension
        )
