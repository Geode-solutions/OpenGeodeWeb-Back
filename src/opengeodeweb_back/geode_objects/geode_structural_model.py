# Standard library imports
from __future__ import annotations

# Third party imports
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_inspector as og_inspector
import geode_viewables as viewables

# Local application imports
from .types import GeodeModelType
from .geode_brep import GeodeBRep


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

    @classmethod
    def geode_object_type(cls) -> GeodeModelType:
        return "StructuralModel"

    def native_extension(self) -> str:
        return self.structural_model.native_extension()

    def builder(self) -> og_geosciences.StructuralModelBuilder:
        return og_geosciences.StructuralModelBuilder(self.structural_model)

    @classmethod
    def load(cls, filename: str) -> GeodeStructuralModel:
        return GeodeStructuralModel(og_geosciences.load_structural_model(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og_geosciences.structural_model_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og_geosciences.is_structural_model_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og_geosciences.StructuralModelInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og_geosciences.StructuralModelOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og_geosciences.structural_model_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og_geosciences.is_structural_model_saveable(
            self.structural_model, filename
        )

    def save(self, filename: str) -> list[str]:
        return og_geosciences.save_structural_model(self.structural_model, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_structural_model(
            self.structural_model, filename_without_extension
        )

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_structural_model(
            self.structural_model, filename_without_extension
        )
