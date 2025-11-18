import opengeode as og
import geode_viewables as viewables

from .geode_object import GeodeObject, GeodeType, ViewerType


class GeodeBRep(GeodeObject):
    brep: og.BRep

    def __init__(self, brep: og.BRep | None = None) -> None:
        self.brep = brep if brep is not None else og.BRep()
        super().__init__(self.brep)

    @classmethod
    def geode_type(cls) -> GeodeType:
        return "BRep"

    @classmethod
    def viewer_type(cls) -> ViewerType:
        return "model"

    def native_extension(self) -> str:
        return self.brep.native_extension()

    @classmethod
    def is_3D(cls) -> bool:
        return True

    @classmethod
    def is_viewable(cls) -> bool:
        return True

    def builder(self) -> og.BRepBuilder:
        return og.BRepBuilder(self.brep)

    @classmethod
    def load(self, filename: str) -> "GeodeBRep":
        return GeodeBRep(og.load_brep(filename))

    @classmethod
    def additional_files(cls, filename: str) -> og.AdditionalFiles:
        return og.brep_additional_files(filename)

    @classmethod
    def is_loadable(cls, filename: str) -> og.Percentage:
        return og.is_brep_loadable(filename)

    @classmethod
    def input_extensions(cls) -> list[str]:
        return og.BRepInputFactory.list_creators()

    @classmethod
    def output_extensions(cls) -> list[str]:
        return og.BRepOutputFactory.list_creators()

    @classmethod
    def object_priority(cls, filename: str) -> int:
        return og.brep_object_priority(filename)

    def is_saveable(self, filename: str) -> bool:
        return og.is_brep_saveable(self.brep, filename)

    def save(self, filename: str) -> list[str]:
        return og.save_brep(self.brep, filename)

    def save_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_viewable_brep(self.brep, filename_without_extension)

    def save_light_viewable(self, filename_without_extension: str) -> str:
        return viewables.save_light_viewable_brep(self.brep, filename_without_extension)
